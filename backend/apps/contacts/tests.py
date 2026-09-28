import uuid
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from apps.organizations.models import Organization
from apps.companies.models import Company
from apps.contacts.models import Contact

User = get_user_model()


class ContactModelTest(TestCase):
    def setUp(self):
        self.org1 = Organization.objects.create(name="Org One", slug="org-one")
        self.org2 = Organization.objects.create(name="Org Two", slug="org-two")
        self.company1 = Company.objects.create(name="Company Alpha", organization=self.org1)
        self.company2 = Company.objects.create(name="Company Beta", organization=self.org2)
        self.user = User.objects.create_user(
            email="user@orgone.com",
            password="password123",
            organization=self.org1,
        )

    def test_contact_uuid_and_relationships(self):
        contact = Contact.objects.create(
            company=self.company1,
            organization=self.org1,
            full_name="Jane Doe",
            email="jane.doe@alpha.com",
            phone="+1234567890",
            role="Director",
        )
        self.assertIsInstance(contact.id, uuid.UUID)
        self.assertEqual(contact.company, self.company1)
        self.assertEqual(contact.organization, self.org1)
        self.assertIn(contact, self.company1.contacts.all())
        self.assertIn(contact, self.org1.contacts.all())
        self.assertFalse(contact.is_deleted)
        self.assertEqual(contact.role, "Director")

    def test_create_contact_auto_sets_organization_from_company(self):
        contact = Contact.objects.create(
            company=self.company1,
            full_name="Krishna Wanusha",
            email="krishna@alpha.com",
        )
        self.assertEqual(contact.organization, self.org1)
        self.assertEqual(contact.full_name, "Krishna Wanusha")

    def test_contact_organization_mismatch_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            contact = Contact(
                organization=self.org2,
                company=self.company1,
                full_name="Cross Tenant",
                email="cross@alpha.com",
            )
            contact.full_clean()

    def test_phone_validation_optional(self):
        # Phone is optional (empty/blank permitted)
        contact = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="No Phone",
            email="nophone@alpha.com",
            phone="",
        )
        contact.full_clean()
        contact.save()
        self.assertEqual(contact.phone, "")

    def test_phone_validation_valid_digits(self):
        # 8 digits
        c1 = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="Eight Digits",
            email="p8@alpha.com",
            phone="12345678",
        )
        c1.full_clean()

        # 15 digits with international prefix and formatting
        c2 = Contact(
            company=self.company1,
            organization=self.org1,
            full_name="Fifteen Digits",
            email="p15@alpha.com",
            phone="+123456789012345",
        )
        c2.full_clean()

    def test_phone_validation_invalid_digits(self):
        # Too short: 7 digits
        with self.assertRaises(ValidationError):
            c_short = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="Too Short",
                email="short@alpha.com",
                phone="1234567",
            )
            c_short.full_clean()

        # Too long: 16 digits
        with self.assertRaises(ValidationError):
            c_long = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="Too Long",
                email="long@alpha.com",
                phone="1234567890123456",
            )
            c_long.full_clean()

        # No digits
        with self.assertRaises(ValidationError):
            c_nan = Contact(
                company=self.company1,
                organization=self.org1,
                full_name="No Digits",
                email="nan@alpha.com",
                phone="letters-only",
            )
            c_nan.full_clean()

    def test_unique_email_per_company_constraint(self):
        Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Alice Smith",
            email="alice@alpha.com",
        )

        # Model clean check
        with self.assertRaises(ValidationError):
            duplicate_contact = Contact(
                organization=self.org1,
                company=self.company1,
                full_name="Alice Duplicate",
                email="alice@alpha.com",
            )
            duplicate_contact.full_clean()

        # DB constraint check
        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                organization=self.org1,
                company=self.company1,
                full_name="Alice Duplicate",
                email="alice@alpha.com",
            )

    def test_same_email_allowed_in_different_companies(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Bob Taylor",
            email="bob@example.com",
        )
        contact2 = Contact.objects.create(
            organization=self.org2,
            company=self.company2,
            full_name="Bob Taylor",
            email="bob@example.com",
        )
        self.assertEqual(contact1.email, contact2.email)
        self.assertNotEqual(contact1.company, contact2.company)

    def test_soft_delete_allows_recreating_same_email(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Charlie Brown",
            email="charlie@alpha.com",
        )
        contact1.soft_delete(user=self.user)
        self.assertTrue(contact1.is_deleted)
        self.assertEqual(Contact.objects.filter(id=contact1.id).count(), 0)

        # Re-creating same email in the company is allowed since contact1 is deleted
        contact2 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            full_name="Charlie Brown New",
            email="charlie@alpha.com",
        )
        self.assertEqual(contact2.email, "charlie@alpha.com")
        self.assertEqual(Contact.objects.filter(company=self.company1, email="charlie@alpha.com").count(), 1)
        self.assertEqual(Contact.all_objects.filter(company=self.company1, email="charlie@alpha.com").count(), 2)
