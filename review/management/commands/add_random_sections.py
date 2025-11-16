import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Course, Prof, Campus, Section, Teach

class Command(BaseCommand):
    help = 'Creates a specified number of random sections in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            'total',
            type=int,
            help='Indicates the number of random sections to be created.'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        total = kwargs['total']
        fake = Faker()

        # --- Fetch existing data for relationships ---
        courses = list(Course.objects.all())
        profs = list(Prof.objects.all())
        campuses = list(Campus.objects.all())

        # --- Validate that required data exists ---
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found. Please create courses first.'))
            return
        if not profs:
            self.stdout.write(self.style.ERROR('No professors found. Please create professors first.'))
            return
        if not campuses:
            self.stdout.write(self.style.ERROR('No campuses found. Please create campuses first.'))
            return

        self.stdout.write(f"Starting to create {total} random sections...")

        created_count = 0
        for i in range(total):
            random_course = random.choice(courses)
            random_prof = random.choice(profs)
            random_campus = random.choice(campuses)

            # Generate a unique section number for the course
            section_number = f"{random.randint(1, 10):02d}"
            if Section.objects.filter(course=random_course, section_number=section_number).exists():
                # If it exists, try another number or skip. For simplicity, we'll just log and continue.
                self.stdout.write(self.style.WARNING(f"Section {section_number} for {random_course.course_code} already exists. Skipping."))
                continue

            # --- Create the Section ---
            section = Section.objects.create(
                course=random_course,
                section_number=section_number,
                campus=random_campus,
                datetime=f"{random.choice(['Mon', 'Tue', 'Wed', 'Thu', 'Fri'])} {random.randint(8, 16)}:00-{random.randint(9, 17)}:00",
                room=f"{fake.building_number()}-{random.randint(101, 505)}"
            )

            # --- Create the Teaching assignment (M2M through 'Teach') ---
            Teach.objects.create(
                prof=random_prof,
                section=section
            )
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} random sections.'))