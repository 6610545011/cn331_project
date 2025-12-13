import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Course, Prof, Campus, Section, Teach, TimeSlot, SectionTime

class Command(BaseCommand):
    help = 'Creates random sections (1-5 per course) with teaching assignments.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write("Deleting all existing Section records...")
        delete_result = Section.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} sections.")

        self.stdout.write("Deleting all existing TimeSlot records...")
        TimeSlot.objects.all().delete()

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

        self.stdout.write("Creating time slots...")
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        times = ['08:00', '10:00', '12:00', '14:00', '16:00']
        time_slots = []
        for day in days:
            for time in times:
                end_time = f"{int(time.split(':')[0]) + 1}:00"
                time_slots.append(TimeSlot(time=f"{day} {time}-{end_time}"))
        TimeSlot.objects.bulk_create(time_slots)
        available_timeslots = list(TimeSlot.objects.all())

        self.stdout.write("Creating sections...")

        section_count = 0
        for course in courses:
            # Random number of sections per course (1-5)
            num_sections = random.randint(1, 5)
            
            for sec_num in range(1, num_sections + 1):
                section_number = f"{sec_num:02d}"
                random_campus = random.choice(campuses)
                random_timeslot = random.choice(available_timeslots)
                room = f"{random.choice(['A', 'B', 'C'])}-{random.randint(100, 500)}"

                section = Section.objects.create(
                    course=course,
                    section_number=section_number,
                    campus=random_campus,
                    datetime=random_timeslot.time,
                    room=room
                )

                # Link section with time slot using SectionTime through model
                SectionTime.objects.create(section=section, slot=random_timeslot)

                # Assign 1 professor to this section
                assigned_prof = random.choice(profs)
                Teach.objects.create(
                    prof=assigned_prof,
                    section=section
                )

                section_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {section_count} random sections with teaching assignments.'))
