import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Course, Prof, Section, Campus, Teach
from .models import Review
from review.forms import ReviewForm
from review.models import ReviewUpvote, Report, Bookmark

User = get_user_model()

class WriteReviewViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')
        self.campus = Campus.objects.create(name='Test Campus')
        self.course = Course.objects.create(course_code='CS331', course_name='Software Engineering', credit=3)
        self.professor = Prof.objects.create(
            prof_name='Dr. Test',
            description='A test professor.'
        )
        self.section = Section.objects.create(
            course=self.course,
            section_number='701',
            campus=self.campus,
            datetime='Mon 10:00-12:00',
            room='Main Building'
        )
        self.section.teachers.add(self.professor)
        self.section.students.add(self.user)
        self.client = Client()
        self.write_review_url = reverse('review:write_review')

    def test_write_review_page_redirects_if_not_logged_in(self):
        response = self.client.get(self.write_review_url)
        self.assertEqual(response.status_code, 302)

    def test_write_review_page_loads_for_logged_in_user(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.write_review_url)
        self.assertEqual(response.status_code, 200)

    def test_write_review_submission_successful(self):
        self.client.login(username='testuser', password='testpassword123')
        self.assertEqual(Review.objects.count(), 0)
        review_data = {
            'course': self.course.id,
            'section': self.section.id,
            'prof': self.professor.id,
            'rating': 5,
            'header': 'Great course!',
            'body': 'Learned a lot.',
            'incognito': False,
        }
        response = self.client.post(self.write_review_url, data=review_data)
        self.assertRedirects(response, reverse('core:homepage'))
        self.assertEqual(Review.objects.count(), 1)

    def test_write_review_submission_missing_rating(self):
        self.client.login(username='testuser', password='testpassword123')
        invalid_data = {
            'course': self.course.id,
            'section': self.section.id,
            'prof': self.professor.id,
            'header': 'Incomplete',
            'body': 'Forgot rating.',
        }
        response = self.client.post(self.write_review_url, data=invalid_data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertIn('rating', response.context['form'].errors)

    def test_write_review_submission_with_nonexistent_section(self):
        self.client.login(username='testuser', password='testpassword123')
        invalid_data = {
            'course': self.course.id,
            'section': '999',
            'prof': self.professor.id,
            'rating': 4,
            'header': 'Wrong section',
            'body': 'Testing fake section.',
        }
        response = self.client.post(self.write_review_url, data=invalid_data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertIn('section', response.context['form'].errors)

    def test_incognito_review_is_saved_correctly(self):
        """
        Test (Good Path): Ensure that when 'incognito' is checked,
        the review is saved with incognito=True.
        """
        self.client.login(username='testuser', password='testpassword123')
        review_data = {
            'course': self.course.id,
            'section': self.section.id,
            'prof': self.professor.id,
            'rating': 4,
            'header': 'Anonymous Review',
            'body': 'This is an incognito review.',
            'incognito': 'on',  # HTML checkbox sends 'on' when checked
        }
        self.client.post(self.write_review_url, data=review_data)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertTrue(review.incognito, "Review should be saved as incognito.")


class ReviewAPIsTestCase(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='API Test Campus')
        self.course1 = Course.objects.create(course_code='CS101', course_name='Intro to CS', credit=3)
        self.course2 = Course.objects.create(course_code='MA202', course_name='Calculus II', credit=3) # Add another course for testing
        self.prof1 = Prof.objects.create(
            prof_name='Prof. Turing',
            description='API test professor.'
        )
        self.prof2 = Prof.objects.create( # Add another professor
            prof_name='Prof. Knuth',
            description='Another API test professor.'
        )
        self.sec1 = Section.objects.create(
            course=self.course1,
            section_number='01',
            campus=self.campus,
            datetime='Tue 13:00-15:00',
            room='CS Building'
        )
        self.sec1.teachers.add(self.prof1)
        self.sec1.teachers.add(self.prof2) # Add both to same section to test list
        # Section 2 for the same course but different professor
        self.sec2 = Section.objects.create(
            course=self.course1,
            section_number='02',
            campus=self.campus,
            datetime='Wed 10:00-12:00',
            room='CS Building'
        )
        self.sec2.teachers.add(self.prof2)
        self.client = Client()

    def test_search_courses_api(self):
        url = reverse('review:ajax_search_courses')
        response = self.client.get(url, {'term': 'CS'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_get_professors_for_course_api(self):
        url = reverse('review:ajax_get_professors')
        params = {'section_id': self.sec1.id}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('professors', data)
        self.assertEqual(len(data['professors']), 2) # Should find 2 professors for CS101
        professor_names = {p['name'] for p in data['professors']}
        self.assertIn('Prof. Turing', professor_names)
        self.assertIn('Prof. Knuth', professor_names)

    def test_search_courses_api_no_results(self):
        """
        Test (Sad Path): Ensure the search API returns an empty list
        when no courses match the search term.
        """
        url = reverse('review:ajax_search_courses')
        response = self.client.get(url, {'term': 'XYZ'}) # Search for a term that doesn't exist
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0, "Should return an empty list for no matches.")

    def test_get_professors_for_course_api_invalid_id(self):
        """
        Test (Sad Path): Ensure the professors API returns an empty list
        when an invalid or non-existent course_id is provided.
        """
        url = reverse('review:ajax_get_professors')
        params = {'section_id': 999} # Use an ID that doesn't exist
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('professors', data)
        self.assertEqual(len(data['professors']), 0, "Should return an empty list for an invalid section ID.")


class ReviewFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='p')
        self.course = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        self.prof = Prof.objects.create(prof_name="Dr. Smith")
        self.section = Section.objects.create(course=self.course, section_number="01")
        self.section.teachers.add(self.prof)
        self.section.students.add(self.user)

    def test_form_valid(self):
        form = ReviewForm(data={
            'course': self.course.id,
            'section': self.section.id,
            'prof': self.prof.id,
            'header': 'H',
            'body': 'B',
            'rating': 5
        }, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_no_target(self):
        form = ReviewForm(data={'header': 'H', 'body': 'B', 'rating': 5}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_form_mismatch_section_course(self):
        c2 = Course.objects.create(course_code="CS102", credit=3)
        form = ReviewForm(data={
            'course': c2.id,
            'section': self.section.id,
            'header': 'H', 'body': 'B', 'rating': 5
        }, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('section', form.errors)

    def test_form_infer_course(self):
        form = ReviewForm(data={
            'prof': self.prof.id,
            'header': 'H', 'body': 'B', 'rating': 5
        }, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['course'], self.course)

class ReviewActionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='p')
        self.client.login(username='u', password='p')
        self.course = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        self.review = Review.objects.create(user=self.user, course=self.course, head='H', body='B', rating=5)

    def test_toggle_bookmark(self):
        resp = self.client.post(reverse('review:toggle_bookmark', args=[self.review.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Bookmark.objects.filter(user=self.user, review=self.review).exists())

    def test_report_review(self):
        resp = self.client.post(reverse('review:report_review', args=[self.review.id]), {'comment': 'Bad'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Report.objects.filter(review=self.review).exists())
        
        resp = self.client.post(reverse('review:report_review', args=[self.review.id]), {'comment': 'Bad'})
        self.assertEqual(resp.status_code, 409)

    def test_vote_review(self):
        import json
        resp = self.client.post(reverse('review:vote_review', args=[self.review.id]), 
                                data=json.dumps({'vote_type': 1}), 
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['user_vote'], 1)
        
        resp = self.client.post(reverse('review:vote_review', args=[self.review.id]), 
                                data=json.dumps({'vote_type': 1}), 
                                content_type='application/json')
        self.assertEqual(resp.json()['user_vote'], 0)

    def test_delete_review(self):
        resp = self.client.post(reverse('review:delete_review', args=[self.review.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Review.objects.filter(id=self.review.id).exists())

    def test_ajax_views(self):
        s = Section.objects.create(course=self.course, section_number="01")
        p = Prof.objects.create(prof_name="Dr. Smith")
        from core.models import Teach
        Teach.objects.create(prof=p, section=s)
        
        resp = self.client.get(reverse('review:ajax_get_professors'), {'section_id': s.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['professors']), 1)
        
        resp = self.client.get(reverse('review:ajax_get_sections'), {'course_id': self.course.id})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['sections']), 1)