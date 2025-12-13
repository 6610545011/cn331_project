import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Course, Prof, Campus, Section, Teach


class Command(BaseCommand):
    help = 'Ensure each course has X sections (numbered 01..X) and assign a random professor to each section.'

    def add_arguments(self, parser):
        parser.add_argument(
            'per_course',
            type=int,
            help='Number of sections to ensure per course (sections numbered 01..X).'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        per_course = kwargs['per_course']
        fake = Faker()

        courses = list(Course.objects.all())
        profs = list(Prof.objects.all())
        campuses = list(Campus.objects.all())

        if not courses:
            self.stdout.write(self.style.ERROR('No courses found. Create courses first.'))
            return
        if not profs:
            self.stdout.write(self.style.ERROR('No professors found. Create professors first.'))
            return
        if not campuses:
            self.stdout.write(self.style.ERROR('No campuses found. Create campuses first.'))
            return

        created_sections = 0
        created_teaches = 0

        self.stdout.write(f"Ensuring each course has {per_course} sections (01..{per_course:02d})...")

        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

        for course in courses:
            for n in range(1, per_course + 1):
                section_number = f"{n:02d}"

                # If section already exists for this course & number, skip creation
                if Section.objects.filter(course=course, section_number=section_number).exists():
                    continue

                random_prof = random.choice(profs)
                random_campus = random.choice(campuses)

                # Random schedule: day + start/end time
                day = random.choice(days)
                start_hour = random.randint(8, 16)
                duration_hours = random.choice([1, 2])
                end_hour = min(20, start_hour + duration_hours)
                minute = random.choice([0, 30])
                datetime_str = f"{day} {start_hour:02d}:{minute:02d}-{end_hour:02d}:{minute:02d}"

                room = f"{fake.building_number()}-{random.randint(100, 599)}"

                section = Section.objects.create(
                    course=course,
                    section_number=section_number,
                    campus=random_campus,
                    datetime=datetime_str,
                    room=room,
                )
                created_sections += 1

                # Create a single Teach assignment linking a random professor to this section
                Teach.objects.create(prof=random_prof, section=section)
                created_teaches += 1

        self.stdout.write(self.style.SUCCESS(f'Created {created_sections} sections and {created_teaches} teaching assignments.'))
