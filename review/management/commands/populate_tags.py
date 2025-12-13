from django.core.management.base import BaseCommand
from review.models import Tag

class Command(BaseCommand):
    help = 'Creates 5 review tags.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Tag records...")
        delete_result = Tag.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} tags.")

        self.stdout.write("Creating new tag records...")
        
        tag_names = [
            "Exam",
            "Homework",
            "Attendance",
            "Teaching Quality",
            "Course Content"
        ]
        
        items = [Tag(name=name) for name in tag_names]
        
        Tag.objects.bulk_create(items)
        
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new tags."))
