from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db import transaction
from django.urls import reverse

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


class ReviewFormTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='formuser', email='form@example.com', password='pass')
        self.campus = Campus.objects.create(name='Form Campus')
        self.course = Course.objects.create(course_code='CS400', course_name='Testing', credit=3)
        self.prof = Prof.objects.create(prof_name='Prof Form', email='pform@example.com')
        self.section = Section.objects.create(section_number='01', course=self.course, campus=self.campus)
        from core.models import Teach, Enrollment
        Teach.objects.create(prof=self.prof, section=self.section)
        Enrollment.objects.create(user=self.user, section=self.section)

    def test_review_form_valid(self):
        from review.forms import ReviewForm
        form_data = {
            'course': self.course.id,
            'section': self.section.id,
            'prof': self.prof.id,
            'header': 'Good test',
            'body': 'Great course',
            'rating': 5,
            'incognito': False,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_review_form_no_target(self):
        from review.forms import ReviewForm
        form_data = {
            'course': None,
            'prof': None,
            'header': 'No target',
            'body': 'Test',
            'rating': 3,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())
        # Check that validation error is raised
        self.assertTrue(len(form.non_field_errors()) > 0)

    def test_review_form_section_not_in_course(self):
        from review.forms import ReviewForm
        course2 = Course.objects.create(course_code='MA500', course_name='Math', credit=3)
        section2 = Section.objects.create(section_number='02', course=course2, campus=self.campus)
        form_data = {
            'course': self.course.id,
            'section': section2.id,
            'prof': self.prof.id,
            'header': 'Mismatch',
            'body': 'Test',
            'rating': 4,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_review_form_prof_not_teaching_course(self):
        from review.forms import ReviewForm
        prof2 = Prof.objects.create(prof_name='Prof Unrelated', email='unrelated@example.com')
        form_data = {
            'course': self.course.id,
            'prof': prof2.id,
            'header': 'Wrong prof',
            'body': 'Test',
            'rating': 2,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_review_form_prof_not_teaching_section(self):
        from review.forms import ReviewForm
        prof2 = Prof.objects.create(prof_name='Prof Other', email='other@example.com')
        form_data = {
            'section': self.section.id,
            'prof': prof2.id,
            'header': 'Wrong prof section',
            'body': 'Test',
            'rating': 3,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_review_form_prof_only_infers_course(self):
        from review.forms import ReviewForm
        form_data = {
            'prof': self.prof.id,
            'header': 'Prof only',
            'body': 'Test',
            'rating': 4,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertIsNotNone(form.cleaned_data['course'])

    def test_review_form_prof_without_course_no_inference(self):
        from review.forms import ReviewForm
        prof_orphan = Prof.objects.create(prof_name='Prof Orphan', email='orphan@example.com')
        form_data = {
            'prof': prof_orphan.id,
            'header': 'Orphan prof',
            'body': 'Test',
            'rating': 3,
        }
        form = ReviewForm(data=form_data, user=self.user)
        self.assertFalse(form.is_valid())

    def test_report_form_valid(self):
        from review.forms import ReportForm
        form_data = {'comment': 'This is spam'}
        form = ReportForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_reviewupvote_form_valid(self):
        from review.forms import ReviewUpvoteForm
        form_data = {'vote_type': 1}
        form = ReviewUpvoteForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_reviewupvote_form_invalid_vote(self):
        from review.forms import ReviewUpvoteForm
        form_data = {'vote_type': 5}
        form = ReviewUpvoteForm(data=form_data)
        self.assertFalse(form.is_valid())


class ReviewViewsTestCase(TestCase):
    def setUp(self):
        self.client = self.client
        self.user = User.objects.create_user(username='viewuser', email='vuser@example.com', password='pw')
        self.client.force_login(self.user)
        self.campus = Campus.objects.create(name='View Campus')
        self.course = Course.objects.create(course_code='CS500', course_name='Views', credit=3)
        self.prof = Prof.objects.create(prof_name='Prof View', email='pview@example.com')
        self.section = Section.objects.create(section_number='01', course=self.course, campus=self.campus)
        from core.models import Teach, Enrollment
        Teach.objects.create(prof=self.prof, section=self.section)
        Enrollment.objects.create(user=self.user, section=self.section)
        self.review = Review.objects.create(user=self.user, course=self.course, head='Test', body='Body', rating=5)

    def test_write_review_get(self):
        resp = self.client.get(reverse('review:write_review'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)

    def test_write_review_post_valid(self):
        data = {
            'course': self.course.id,
            'prof': self.prof.id,
            'header': 'New Review',
            'body': 'Test body',
            'rating': 4,
            'incognito': False,
        }
        resp = self.client.post(reverse('review:write_review'), data)
        self.assertRedirects(resp, reverse('core:homepage'))
        self.assertTrue(Review.objects.filter(head='New Review').exists())

    def test_write_review_post_invalid(self):
        data = {
            'header': 'Invalid',
            'body': 'No course or prof',
            'rating': 2,
        }
        resp = self.client.post(reverse('review:write_review'), data)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('form', resp.context)
        self.assertFalse(resp.context['form'].is_valid())

    def test_write_review_redirect_if_not_logged_in(self):
        self.client.logout()
        resp = self.client.get(reverse('review:write_review'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.url)

    def test_ajax_search_courses(self):
        url = reverse('review:ajax_search_courses')
        resp = self.client.get(url, {'term': 'CS'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('results', data)

    def test_ajax_get_professors(self):
        url = reverse('review:ajax_get_professors')
        resp = self.client.get(url, {'section_id': self.section.id})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('professors', data)
        self.assertEqual(len(data['professors']), 1)

    def test_ajax_get_sections(self):
        url = reverse('review:ajax_get_sections')
        resp = self.client.get(url, {'course_id': self.course.id})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('sections', data)

    def test_toggle_bookmark_create(self):
        url = reverse('review:toggle_bookmark', args=[self.review.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['bookmarked'])
        self.assertTrue(Bookmark.objects.filter(user=self.user, review=self.review).exists())

    def test_toggle_bookmark_delete(self):
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        url = reverse('review:toggle_bookmark', args=[self.review.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data['bookmarked'])

    def test_report_review_valid(self):
        url = reverse('review:report_review', args=[self.review.id])
        data = {'comment': 'Inappropriate'}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(resp_data['status'], 'ok')
        self.assertTrue(Report.objects.filter(user=self.user, review=self.review).exists())

    def test_report_review_duplicate(self):
        Report.objects.create(user=self.user, review=self.review, comment='First report')
        url = reverse('review:report_review', args=[self.review.id])
        data = {'comment': 'Duplicate report'}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 409)
        resp_data = resp.json()
        self.assertEqual(resp_data['status'], 'error')

    def test_vote_review_upvote(self):
        import json
        url = reverse('review:vote_review', args=[self.review.id])
        data = json.dumps({'vote_type': 1})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(resp_data['user_vote'], 1)

    def test_vote_review_downvote(self):
        import json
        url = reverse('review:vote_review', args=[self.review.id])
        data = json.dumps({'vote_type': -1})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(resp_data['user_vote'], -1)

    def test_vote_review_toggle(self):
        import json
        url = reverse('review:vote_review', args=[self.review.id])
        # First upvote
        data = json.dumps({'vote_type': 1})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # Toggle same vote
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        resp_data = resp.json()
        self.assertEqual(resp_data['user_vote'], 0)

    def test_vote_review_invalid_json(self):
        url = reverse('review:vote_review', args=[self.review.id])
        resp = self.client.post(url, 'invalid json', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_vote_review_invalid_vote_type(self):
        import json
        url = reverse('review:vote_review', args=[self.review.id])
        data = json.dumps({'vote_type': 99})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_vote_review_update_vote_type(self):
        """Test changing vote from upvote to downvote"""
        import json
        url = reverse('review:vote_review', args=[self.review.id])
        # First upvote
        data = json.dumps({'vote_type': 1})
        resp = self.client.post(url, data, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        # Change to downvote
        data = json.dumps({'vote_type': -1})
        resp = self.client.post(url, data, content_type='application/json')
        resp_data = resp.json()
        self.assertEqual(resp_data['user_vote'], -1)

    def test_delete_review_own_review(self):
        url = reverse('review:delete_review', args=[self.review.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_delete_review_others_review_fails(self):
        other_user = User.objects.create_user(username='other', email='other@example.com', password='pw')
        other_review = Review.objects.create(user=other_user, course=self.course, head='Other', body='Body', rating=3)
        url = reverse('review:delete_review', args=[other_review.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Review.objects.filter(id=other_review.id).exists())

    def test_ajax_search_courses_empty_result(self):
        url = reverse('review:ajax_search_courses')
        resp = self.client.get(url, {'term': 'NONEXISTENT'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['results']), 0)

    def test_ajax_get_professors_no_section(self):
        url = reverse('review:ajax_get_professors')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['professors']), 0)

    def test_ajax_get_sections_no_course(self):
        url = reverse('review:ajax_get_sections')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data['sections']), 0)

