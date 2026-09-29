from django.core.management.base import BaseCommand
from django.db import transaction
from django_multitenant.utils import set_current_tenant, unset_current_tenant
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.companies.models import Company
from apps.contacts.models import Contact
from apps.activity_logs.models import ActivityLog


class Command(BaseCommand):
    help = "Seeds organizations, users (Admin, Manager, Staff), companies, and contacts for development and testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean existing CRM seed data before seeding.",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="Password123!",
            help="Default password for seeded users (default: Password123!).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        clean = options["clean"]
        default_pwd = options["password"]

        self.stdout.write(self.style.NOTICE("==> Seeding CRM database with test organizations, users, and data..."))

        if clean:
            self.stdout.write("Cleaning existing companies, contacts, and users...")
            Contact.objects.all().delete()
            Company.objects.all().delete()
            ActivityLog.objects.all().delete()
            User.objects.all().delete()
            Organization.objects.all().delete()

        # Organizations
        org_alpha, created = Organization.objects.get_or_create(
            slug="alpha-corp",
            defaults={
                "name": "Alpha Corporation",
                "subscription_plan": Organization.SubscriptionPlan.PRO,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created organization: {org_alpha.name} (alpha-corp) - Plan: {org_alpha.subscription_plan}"))
        else:
            org_alpha.subscription_plan = Organization.SubscriptionPlan.PRO
            org_alpha.save(update_fields=["subscription_plan"])
            self.stdout.write(f"Organization already exists: {org_alpha.name} - Plan: {org_alpha.subscription_plan}")

        org_beta, created = Organization.objects.get_or_create(
            slug="beta-solutions",
            defaults={
                "name": "Beta Solutions Ltd",
                "subscription_plan": Organization.SubscriptionPlan.BASIC,
                "is_active": True,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created organization: {org_beta.name} (beta-solutions) - Plan: {org_beta.subscription_plan}"))
        else:
            org_beta.subscription_plan = Organization.SubscriptionPlan.BASIC
            org_beta.save(update_fields=["subscription_plan"])
            self.stdout.write(f"Organization already exists: {org_beta.name} - Plan: {org_beta.subscription_plan}")

        # Users for Organization Alpha
        users_to_seed = [
            {
                "email": "admin@alphacorp.com",
                "first_name": "Alice",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "organization": org_alpha,
                "is_staff": True,
                "is_superuser": True,
            },
            {
                "email": "manager@alphacorp.com",
                "first_name": "Mark",
                "last_name": "Manager",
                "role": User.Role.MANAGER,
                "organization": org_alpha,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "staff@alphacorp.com",
                "first_name": "Sam",
                "last_name": "Staff",
                "role": User.Role.STAFF,
                "organization": org_alpha,
                "is_staff": False,
                "is_superuser": False,
            },
            {
                "email": "admin@betasolutions.com",
                "first_name": "Bob",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "organization": org_beta,
                "is_staff": True,
                "is_superuser": False,
            },
        ]

        created_users = {}
        for user_data in users_to_seed:
            email = user_data["email"]
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create_user(
                    email=email,
                    password=default_pwd,
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    role=user_data["role"],
                    organization=user_data["organization"],
                    is_staff=user_data["is_staff"],
                    is_superuser=user_data["is_superuser"],
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(f"Created user: {email} ({user.role}) - Org: {user.organization.name}"))
            else:
                user.set_password(default_pwd)
                user.role = user_data["role"]
                user.organization = user_data["organization"]
                user.is_staff = user_data["is_staff"]
                user.is_superuser = user_data["is_superuser"]
                user.is_active = True
                user.save()
                self.stdout.write(f"Updated user: {email} ({user.role})")
            created_users[email] = user

        alpha_admin = created_users["admin@alphacorp.com"]
        beta_admin = created_users["admin@betasolutions.com"]

        # Companies & Contacts for Alpha Corporation
        try:
            set_current_tenant(org_alpha)
            comp_acme, _ = Company.objects.get_or_create(
                organization=org_alpha,
                name="Acme Dynamics",
                defaults={
                    "industry": "Technology",
                    "country": "US",
                    "website": "https://acmedynamics.com",
                    "phone": "+12025550143",
                    "address": "123 Innovation Way, Suite 400, San Francisco, CA",
                    "is_deleted": False,
                },
            )

            Contact.objects.get_or_create(
                organization=org_alpha,
                company=comp_acme,
                email="jane.smith@acmedynamics.com",
                defaults={
                    "full_name": "Jane Smith",
                    "phone": "+12025550188",
                    "role": "VP of Engineering",
                    "is_deleted": False,
                },
            )

            Contact.objects.get_or_create(
                organization=org_alpha,
                company=comp_acme,
                email="david.miller@acmedynamics.com",
                defaults={
                    "full_name": "David Miller",
                    "phone": "+12025550199",
                    "role": "Head of Procurement",
                    "is_deleted": False,
                },
            )

            comp_logistics, _ = Company.objects.get_or_create(
                organization=org_alpha,
                name="Global Apex Logistics",
                defaults={
                    "industry": "Logistics & Supply Chain",
                    "country": "DE",
                    "website": "https://globalapex.de",
                    "phone": "+493012345678",
                    "address": "Hafenstrasse 42, 20457 Hamburg",
                    "is_deleted": False,
                },
            )

            Contact.objects.get_or_create(
                organization=org_alpha,
                company=comp_logistics,
                email="hans.becker@globalapex.de",
                defaults={
                    "full_name": "Hans Becker",
                    "phone": "+493012345600",
                    "role": "Operations Director",
                    "is_deleted": False,
                },
            )

            # Audit log entries
            if not ActivityLog.objects.filter(organization=org_alpha).exists():
                ActivityLog.objects.create(
                    organization=org_alpha,
                    user=alpha_admin,
                    action=ActivityLog.Action.CREATE,
                    model_name="Company",
                    object_id=str(comp_acme.id),
                    details={"name": comp_acme.name, "seeded": True},
                )
                ActivityLog.objects.create(
                    organization=org_alpha,
                    user=alpha_admin,
                    action=ActivityLog.Action.CREATE,
                    model_name="Company",
                    object_id=str(comp_logistics.id),
                    details={"name": comp_logistics.name, "seeded": True},
                )
        finally:
            unset_current_tenant()

        # Companies & Contacts for Beta Solutions
        try:
            set_current_tenant(org_beta)
            comp_nexus, _ = Company.objects.get_or_create(
                organization=org_beta,
                name="Nexus Healthcare Innovations",
                defaults={
                    "industry": "Healthcare",
                    "country": "GB",
                    "website": "https://nexushealth.co.uk",
                    "phone": "+442079460912",
                    "address": "10 Regent Street, London, UK",
                    "is_deleted": False,
                },
            )

            Contact.objects.get_or_create(
                organization=org_beta,
                company=comp_nexus,
                email="sarah.connor@nexushealth.co.uk",
                defaults={
                    "full_name": "Sarah Connor",
                    "phone": "+442079460933",
                    "role": "Chief Medical Officer",
                    "is_deleted": False,
                },
            )

            if not ActivityLog.objects.filter(organization=org_beta).exists():
                ActivityLog.objects.create(
                    organization=org_beta,
                    user=beta_admin,
                    action=ActivityLog.Action.CREATE,
                    model_name="Company",
                    object_id=str(comp_nexus.id),
                    details={"name": comp_nexus.name, "seeded": True},
                )
        finally:
            unset_current_tenant()

        self.stdout.write(self.style.SUCCESS("\n==> CRM Data Seeding Completed Successfully!"))
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("Credentials Summary (Password: " + default_pwd + ")")
        self.stdout.write("=" * 70)
        self.stdout.write(f"Organization: Alpha Corporation (alpha-corp)")
        self.stdout.write(f"  • ADMIN:   admin@alphacorp.com")
        self.stdout.write(f"  • MANAGER: manager@alphacorp.com")
        self.stdout.write(f"  • STAFF:   staff@alphacorp.com")
        self.stdout.write("-" * 70)
        self.stdout.write(f"Organization: Beta Solutions Ltd (beta-solutions) [Isolated Tenant]")
        self.stdout.write(f"  • ADMIN:   admin@betasolutions.com")
        self.stdout.write("=" * 70 + "\n")
