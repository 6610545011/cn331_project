from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from faker import Faker
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates 50 random users with disabled passwords.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing User records (except superusers)...")
        delete_result = User.objects.filter(is_superuser=False).delete()
        self.stdout.write(f"Removed {delete_result[0]} users.")

        fake = Faker()
        
        self.stdout.write("Creating new user records...")
        
        items = []
        used_usernames = set()
        used_emails = set()
        
        for i in range(50):
            first_name = fake.first_name()
            last_name = fake.last_name()
            
            # Username: firstname space lastname
            username = f"{first_name} {last_name}"
            counter = 1
            original_username = username
            while username in used_usernames:
                username = f"{original_username}{counter}"
                counter += 1
            used_usernames.add(username)
            
            # Email: firstnamelastname@example.mail
            email = f"{first_name.lower()}{last_name.lower()}@example.mail"
            counter = 1
            original_email_base = email[:-13]  # remove @example.mail
            while email in used_emails:
                email = f"{original_email_base}{counter}@example.mail"
                counter += 1
            used_emails.add(email)
            
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_staff=False
            )
            # Set password to unusable (disabled)
            user.set_unusable_password()
            items.append(user)
        
        # Bulk create users
        User.objects.bulk_create(items)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new users with disabled passwords."))
