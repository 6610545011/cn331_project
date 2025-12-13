import random
from datetime import time
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Section
from planner.models import SectionSchedule


class Command(BaseCommand):
    help = 'Generate random schedules for each section using SectionSchedule.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        sections = list(Section.objects.all())

        if not sections:
            self.stdout.write(self.style.ERROR('No sections found. Create sections first.'))
            return

        self.stdout.write(f"Generating random schedules for {len(sections)} sections...")

        # Common time slots (start_time, end_time) that align to 30-minute slots
        time_slot_options = [
            (time(8, 0), time(9, 0)),
            (time(8, 30), time(9, 30)),
            (time(9, 0), time(10, 0)),
            (time(9, 30), time(10, 30)),
            (time(10, 0), time(11, 0)),
            (time(10, 30), time(11, 30)),
            (time(11, 0), time(12, 0)),
            (time(12, 0), time(13, 0)),
            (time(13, 0), time(14, 0)),
            (time(13, 30), time(14, 30)),
            (time(14, 0), time(15, 0)),
            (time(14, 30), time(15, 30)),
            (time(15, 0), time(16, 0)),
            (time(15, 30), time(16, 30)),
            (time(16, 0), time(17, 0)),
        ]

        created_count = 0

        for section in sections:
            # Generate 2-3 random days per section
            num_days = random.randint(2, 3)
            selected_days = random.sample(range(5), num_days)  # 0-4 = Mon-Fri

            for day in selected_days:
                start_time, end_time = random.choice(time_slot_options)

                # Check if this schedule already exists
                if not SectionSchedule.objects.filter(
                    section=section,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time
                ).exists():
                    SectionSchedule.objects.create(
                        section=section,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                    created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} section schedules.'
            )
        )
