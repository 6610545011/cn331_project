from django.core.management.base import BaseCommand
from core.models import Course
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Creates 10 courses with random credits (1-3) and descriptions.'

    def handle(self, *args, **options):
        self.stdout.write("Deleting all existing Course records...")
        delete_result = Course.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} courses.")

        fake = Faker()
        
        self.stdout.write("Creating new course records...")
        
        course_prefixes = ['CS', 'MATH', 'PHYS', 'CHEM', 'ENG', 'HIST', 'BIO', 'ART', 'MUS', 'ECON']
        used_codes = set()
        
        items = []
        for i in range(10):
            # Generate unique course code
            while True:
                code = f"{random.choice(course_prefixes)}{random.randint(100, 599)}"
                if code not in used_codes:
                    used_codes.add(code)
                    break
            
            course_name = fake.sentence(nb_words=4).strip('.')
            description = fake.paragraph(nb_sentences=3)
            credit = random.choice([1, 2, 3])
            
            items.append(Course(
                course_code=code,
                course_name=course_name,
                description=description,
                credit=credit
            ))
        
        Course.objects.bulk_create(items)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(items)} new courses."))
