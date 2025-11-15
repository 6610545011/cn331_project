from django.core.management.base import BaseCommand
from core.models import Campus

class Command(BaseCommand):
    help = 'Creates predefined campus records in the database.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Campus records...")
        delete_result = Campus.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} campuses.")

        self.stdout.write("Creating new campus records...")
        items = [
            Campus(name="Bangkhen"),
            Campus(name="Kamphaeng Saen"),
            Campus(name="Sriracha"),
            Campus(name="Sakon Nakhon"),
        ]

        # Execute the bulk creation
        Campus.objects.bulk_create(items)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new campuses."))