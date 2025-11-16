from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db import transaction

from core.models import Course, Prof, Section, Campus
from review.models import Review, Tag, ReviewUpvote, Bookmark, Report

User = get_user_model()


class ReviewModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', email='u1@example.com', password='pass')
        self.campus = Campus.objects.create(name='Campus A')
        self.course = Course.objects.create(course_code='CS200', course_name='Algorithms', description='', credit=3)
        self.prof = Prof.objects.create(prof_name='Prof Algo', email='algo@example.com')
        self.section = Section.objects.create(section_number='01', course=self.course, campus=self.campus)
        self.tag = Tag.objects.create(name='helpful')
        self.review = Review.objects.create(user=self.user, course=self.course, section=self.section, prof=self.prof, head='Good', body='Nice course', rating=5)
        self.review.tags.add(self.tag)

    def test_review_str_and_tags(self):
        self.assertIn('Review by', str(self.review))
        self.assertIn(self.review, self.tag.reviews.all())

    def test_vote_score_aggregation(self):
        # Add votes
        user2 = User.objects.create_user(username='u2', email='u2@example.com', password='pass')
        ReviewUpvote.objects.create(user=self.user, review=self.review, vote_type=1)
        ReviewUpvote.objects.create(user=user2, review=self.review, vote_type=-1)
        self.review.refresh_from_db()
        self.assertEqual(self.review.vote_score, 0)

    def test_bookmark_and_report_uniqueness(self):
        # Bookmark a course (review can be null but course required)
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        # duplicate bookmark should raise IntegrityError (unique_together)
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Bookmark.objects.create(user=self.user, review=self.review, course=self.course)

        # Report uniqueness
        reporter = User.objects.create_user(username='rep', email='rep@example.com', password='pass')
        Report.objects.create(review=self.review, user=reporter, comment='spam')
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Report.objects.create(review=self.review, user=reporter, comment='spam 2')

    def test_review_without_section(self):
        review_no_sec = Review.objects.create(user=self.user, course=self.course, prof=self.prof, head='Review', body='Test', rating=3)
        self.assertIsNone(review_no_sec.section)

    def test_review_incognito_field(self):
        review_incog = Review.objects.create(user=self.user, course=self.course, head='Anon', body='Secret', rating=4, incognito=True)
        self.assertTrue(review_incog.incognito)

    def test_review_date_created(self):
        self.assertIsNotNone(self.review.date_created)

    def test_multiple_tags_per_review(self):
        tag2 = Tag.objects.create(name='informative')
        tag3 = Tag.objects.create(name='engaging')
        self.review.tags.add(tag2, tag3)
        self.assertEqual(self.review.tags.count(), 3)

    def test_vote_score_all_upvotes(self):
        user2 = User.objects.create_user(username='u3', email='u3@example.com', password='pass')
        user3 = User.objects.create_user(username='u4', email='u4@example.com', password='pass')
        ReviewUpvote.objects.create(user=user2, review=self.review, vote_type=1)
        ReviewUpvote.objects.create(user=user3, review=self.review, vote_type=1)
        self.review.refresh_from_db()
        self.assertEqual(self.review.vote_score, 2)

    def test_vote_score_all_downvotes(self):
        user2 = User.objects.create_user(username='u5', email='u5@example.com', password='pass')
        ReviewUpvote.objects.create(user=user2, review=self.review, vote_type=-1)
        self.review.refresh_from_db()
        self.assertEqual(self.review.vote_score, -1)

    def test_bookmark_review_null(self):
        bookmark = Bookmark.objects.create(user=self.user, review=None, course=self.course)
        self.assertIsNone(bookmark.review)
        self.assertEqual(bookmark.course, self.course)

    def test_report_str(self):
        report = Report.objects.create(review=self.review, user=self.user, comment='Spam content')
        self.assertIn(str(self.review.id), str(report))

    def test_bookmark_str(self):
        bookmark = Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        self.assertIn(self.user.email, str(bookmark))

    def test_reviewupvote_str(self):
        vote = ReviewUpvote.objects.create(user=self.user, review=self.review, vote_type=1)
        self.assertIn(self.user.email, str(vote))

    def test_rating_values(self):
        for rating in [1, 2, 3, 4, 5]:
            review = Review.objects.create(user=self.user, course=self.course, head=f'Rating {rating}', body='Test', rating=rating)
            self.assertEqual(review.rating, rating)

    def test_multiple_reviews_per_user(self):
        review2 = Review.objects.create(user=self.user, course=self.course, head='Second review', body='Another', rating=3)
        self.assertEqual(self.user.reviews.count(), 2)

    def test_review_ordering_by_date(self):
        review2 = Review.objects.create(user=self.user, course=self.course, head='Later', body='Recent', rating=4)
        reviews = Review.objects.all().order_by('-date_created')
        self.assertEqual(reviews[0].head, 'Later')

    def test_tag_unique_name(self):
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Tag.objects.create(name='helpful')

    def test_tag_str(self):
        self.assertEqual(str(self.tag), 'helpful')

