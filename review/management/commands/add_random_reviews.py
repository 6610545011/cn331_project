import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from review.models import Review
from core.models import Course, Section, Prof

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a specified number of random reviews in the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            'total',
            type=int,
            help='Indicates the number of random reviews to be created.'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        total = kwargs['total']
        fake = Faker('th_TH')

        # --- Fetch existing data ---
        users = list(User.objects.all())
        courses = list(Course.objects.all())
        sections = list(Section.objects.select_related('course').all())
        profs = list(Prof.objects.all())

        # --- Validate data exists ---
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create some users first.'))
            return
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found. Please create some courses first.'))
            return
        if not sections and not profs:
            self.stdout.write(self.style.ERROR('No sections or professors found. Cannot create reviews.'))
            return

        self.stdout.write(f"Starting to create {total} random reviews...")

        reviews_to_create = []
        for i in range(total):
            # --- Randomly select base attributes ---
            random_user = random.choice(users)
            random_rating = random.randint(1, 5)
            random_head = fake.sentence(nb_words=6)
            random_body = fake.paragraph(nb_sentences=5)
            random_incognito = random.choice([True, False])
            # Random datetime within the last year
            random_date = timezone.now() - timedelta(days=random.randint(0, 365))

            review_data = {
                'user': random_user,
                'rating': random_rating,
                'head': random_head,
                'body': random_body,
                'incognito': random_incognito,
                'date_created': random_date,
                'course': None,
                'section': None,
                'prof': None,
            }

            # --- Randomly choose review type: (Course+Section) or (Course+Prof) ---
            # Give priority to section-based reviews if sections exist
            choice = 'section' if sections else 'prof'
            if sections and profs:
                choice = random.choice(['section', 'prof'])

            if choice == 'section':
                random_section = random.choice(sections)
                review_data['course'] = random_section.course
                review_data['section'] = random_section
            elif choice == 'prof':
                # This scenario requires a course and a professor
                random_prof = random.choice(profs)
                random_course = random.choice(courses)
                review_data['course'] = random_course
                review_data['prof'] = random_prof
            
            reviews_to_create.append(Review(**review_data))

        # Bulk create for efficiency
        Review.objects.bulk_create(reviews_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total} random reviews.'))
