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
        self.org1 = Organization.objects.create(name="Org One")
        self.org2 = Organization.objects.create(name="Org Two")
        self.company1 = Company.objects.create(name="Company Alpha", organization=self.org1)
        self.company2 = Company.objects.create(name="Company Beta", organization=self.org2)
        self.user = User.objects.create_user(
            email="user@orgone.com",
            password="password123",
            organization=self.org1,
        )

    def test_create_contact_auto_sets_organization(self):
        contact = Contact.objects.create(
            company=self.company1,
            first_name="Krishna",
            last_name="Wanusha",
            email="krishna@alpha.com",
        )
        self.assertEqual(contact.organization, self.org1)
        self.assertEqual(contact.full_name, "Krishna Wanusha")
        self.assertFalse(contact.is_deleted)

    def test_contact_organization_mismatch_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            contact = Contact(
                organization=self.org2,
                company=self.company1,
                first_name="Krishna",
                last_name="Wanusha",
                email="krishna@alpha.com",
            )
            contact.full_clean()

    def test_unique_email_per_company_constraint(self):
        Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            first_name="Alice",
            last_name="Smith",
            email="alice@alpha.com",
        )

        with self.assertRaises(IntegrityError):
            Contact.objects.create(
                organization=self.org1,
                company=self.company1,
                first_name="Alice",
                last_name="Duplicate",
                email="alice@alpha.com",
            )

    def test_same_email_allowed_in_different_companies(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            first_name="Bob",
            last_name="Taylor",
            email="bob@example.com",
        )
        contact2 = Contact.objects.create(
            organization=self.org2,
            company=self.company2,
            first_name="Bob",
            last_name="Taylor",
            email="bob@example.com",
        )
        self.assertEqual(contact1.email, contact2.email)
        self.assertNotEqual(contact1.company, contact2.company)

    def test_soft_delete_allows_recreating_same_email(self):
        contact1 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            first_name="Charlie",
            last_name="Brown",
            email="charlie@alpha.com",
        )
        contact1.soft_delete(user=self.user)
        self.assertTrue(contact1.is_deleted)
        self.assertEqual(Contact.objects.filter(id=contact1.id).count(), 0)

        # Re-creating the same email in the same company is allowed since contact1 is deleted
        contact2 = Contact.objects.create(
            organization=self.org1,
            company=self.company1,
            first_name="Charlie",
            last_name="Brown New",
            email="charlie@alpha.com",
        )
        self.assertEqual(contact2.email, "charlie@alpha.com")
        self.assertEqual(Contact.objects.filter(company=self.company1, email="charlie@alpha.com").count(), 1)
        self.assertEqual(Contact.all_objects.filter(company=self.company1, email="charlie@alpha.com").count(), 2)
