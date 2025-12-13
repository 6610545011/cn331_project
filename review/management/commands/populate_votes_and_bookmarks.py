import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from review.models import Review, ReviewUpvote, Bookmark, Report
from core.models import Course

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates user votes, reports, and bookmarks for reviews.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        fake = Faker()

        self.stdout.write("Deleting all existing ReviewUpvote records...")
        ReviewUpvote.objects.all().delete()

        self.stdout.write("Deleting all existing Report records...")
        Report.objects.all().delete()

        self.stdout.write("Deleting all existing Bookmark records...")
        Bookmark.objects.all().delete()

        # --- Fetch existing data ---
        users = list(User.objects.all())
        reviews = list(Review.objects.all())
        courses = list(Course.objects.all())

        # --- Validate data exists ---
        if not users:
            self.stdout.write(self.style.ERROR('No users found.'))
            return
        if not reviews:
            self.stdout.write(self.style.ERROR('No reviews found.'))
            return
        if not courses:
            self.stdout.write(self.style.ERROR('No courses found.'))
            return

        self.stdout.write("Creating user votes (upvotes/downvotes)...")

        votes_created = 0
        for review in reviews:
            # Each user has a chance to vote on this review
            for user in users:
                # Around 30% chance each user votes on each review
                if random.random() < 0.3:
                    vote_type = random.choice([1, -1])  # 1 for upvote, -1 for downvote
                    try:
                        ReviewUpvote.objects.create(
                            user=user,
                            review=review,
                            vote_type=vote_type
                        )
                        votes_created += 1
                    except:
                        # Handle unique constraint violation (user already voted)
                        pass

        self.stdout.write(f"Created {votes_created} votes.")

        self.stdout.write("Creating review reports...")

        report_reasons = [
            "Inappropriate language or harassment",
            "Spam or irrelevant content",
            "Misinformation or false claims",
            "Copyright violation",
            "Offensive or discriminatory content",
            "Personal attack on instructor",
            "Unverified claims",
            "Threatening behavior",
            "Off-topic discussion",
            "Duplicate review"
        ]

        reports_created = 0
        for review in reviews:
            # Around 5% chance each review gets reported
            if random.random() < 0.05:
                # 1-3 users might report this review
                num_reports = random.randint(1, 3)
                potential_reporters = random.sample(users, min(num_reports, len(users)))
                
                for reporter in potential_reporters:
                    try:
                        Report.objects.create(
                            review=review,
                            user=reporter,
                            comment=random.choice(report_reasons)
                        )
                        reports_created += 1
                    except:
                        # Handle unique constraint violation (user already reported)
                        pass

        self.stdout.write(f"Created {reports_created} reports.")

        self.stdout.write("Creating bookmarks...")

        bookmarks_created = 0
        for user in users:
            # Each user has around 5-15 bookmarks
            num_bookmarks = random.randint(5, 15)
            
            # Randomly choose to bookmark reviews or courses (or mix)
            for _ in range(num_bookmarks):
                random_course = random.choice(courses)
                
                # 70% chance to bookmark a review, 30% to bookmark just the course
                if random.random() < 0.7 and reviews:
                    # Bookmark a review
                    potential_reviews = [r for r in reviews if r.course == random_course]
                    if potential_reviews:
                        random_review = random.choice(potential_reviews)
                        try:
                            Bookmark.objects.create(
                                user=user,
                                review=random_review,
                                course=random_course
                            )
                            bookmarks_created += 1
                        except:
                            # Handle unique constraint violation
                            pass
                else:
                    # Bookmark just the course
                    try:
                        Bookmark.objects.create(
                            user=user,
                            review=None,
                            course=random_course
                        )
                        bookmarks_created += 1
                    except:
                        # Handle unique constraint violation
                        pass

        self.stdout.write(f"Created {bookmarks_created} bookmarks.")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created votes, reports, and bookmarks. '
            f'Total: {votes_created} votes, {reports_created} reports, {bookmarks_created} bookmarks.'
        ))
