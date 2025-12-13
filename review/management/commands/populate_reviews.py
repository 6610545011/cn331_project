import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from review.models import Review, Tag
from core.models import Course, Section, Prof

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates reviews with tags, ratings, and various associations.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write("Deleting all existing Review records...")
        delete_result = Review.objects.all().delete()
        self.stdout.write(f"Removed {delete_result[0]} reviews.")

        # --- Fetch existing data ---
        users = list(User.objects.all())
        courses = list(Course.objects.all())
        sections = list(Section.objects.select_related('course').all())
        profs = list(Prof.objects.all())
        tags = list(Tag.objects.all())

        # --- Validate data exists ---
        if not users:
            self.stdout.write(self.style.ERROR('No users found. Please create users first.'))
            return
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found. Please create courses first.'))
            return
        if not tags:
            self.stdout.write(self.style.ERROR('No tags found. Please create tags first.'))
            return

        self.stdout.write("Creating review records...")

        reviews_to_create = []
        review_tags = []  # Store M2M relationships to be created later

        for i in range(100):  # Create around 100 reviews
            random_user = random.choice(users)
            random_rating = random.randint(1, 5)
            random_head = fake.sentence(nb_words=8).strip('.')
            random_body = fake.paragraph(nb_sentences=4)
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

            # --- Randomly choose review type ---
            # Weighted distribution: more likely to have section
            if sections and random.random() < 0.6:
                # Review with section (which implies course)
                random_section = random.choice(sections)
                review_data['course'] = random_section.course
                review_data['section'] = random_section
            elif profs:
                # Review with professor (and course)
                random_prof = random.choice(profs)
                random_course = random.choice(courses)
                review_data['course'] = random_course
                review_data['prof'] = random_prof
            else:
                # Fallback: just course
                review_data['course'] = random.choice(courses)
            
            reviews_to_create.append(Review(**review_data))

        # Bulk create reviews
        created_reviews = Review.objects.bulk_create(reviews_to_create)

        self.stdout.write("Assigning tags to reviews...")

        # Assign 1-3 random tags to each review
        for review in created_reviews:
            num_tags = random.randint(1, 3)
            selected_tags = random.sample(tags, min(num_tags, len(tags)))
            review.tags.set(selected_tags)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(created_reviews)} reviews with tags.'))
