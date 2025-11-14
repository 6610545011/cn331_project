import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Course, Prof, Section, Campus, RoomMSTeam
from .models import Review

User = get_user_model()

class WriteReviewViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword123')
        self.campus = Campus.objects.create(name='Test Campus')
        self.room = RoomMSTeam.objects.create(name='TestMS', campus=self.campus)
        self.course = Course.objects.create(code='CS331', name='Software Engineering')
        self.professor = Prof.objects.create(
            name='Dr. Test',
            campus=self.campus,
            room=self.room,
            description='A test professor.'
        )
        self.section = Section.objects.create(
            course=self.course,
            section_number='701',
            professor=self.professor,
            campus=self.campus,
            room=self.room,
            date_time='Mon 10:00-12:00',
            location='Main Building'
        )
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
            'section': '701',
            'professor': self.professor.id,
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
            'section': '701',
            'professor': self.professor.id,
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
            'professor': self.professor.id,
            'rating': 4,
            'header': 'Wrong section',
            'body': 'Testing fake section.',
        }
        response = self.client.post(self.write_review_url, data=invalid_data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertIn('__all__', response.context['form'].errors)

    def test_incognito_review_is_saved_correctly(self):
        """
        Test (Good Path): Ensure that when 'incognito' is checked,
        the review is saved with incognito=True.
        """
        self.client.login(username='testuser', password='testpassword123')
        review_data = {
            'course': self.course.id,
            'section': '701',
            'professor': self.professor.id,
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
        self.room = RoomMSTeam.objects.create(name='API Room', campus=self.campus)
        self.course1 = Course.objects.create(code='CS101', name='Intro to CS')
        self.course2 = Course.objects.create(code='MA202', name='Calculus II') # Add another course for testing
        self.prof1 = Prof.objects.create(
            name='Prof. Turing',
            campus=self.campus,
            room=self.room,
            description='API test professor.'
        )
        self.prof2 = Prof.objects.create( # Add another professor
            name='Prof. Knuth',
            campus=self.campus,
            room=self.room,
            description='Another API test professor.'
        )
        self.sec1 = Section.objects.create(
            course=self.course1,
            section_number='01',
            professor=self.prof1,
            campus=self.campus,
            room=self.room,
            date_time='Tue 13:00-15:00',
            location='CS Building'
        )
        # Section 2 for the same course but different professor
        self.sec2 = Section.objects.create(
            course=self.course1,
            section_number='02',
            professor=self.prof2,
            campus=self.campus,
            room=self.room,
            date_time='Wed 10:00-12:00',
            location='CS Building'
        )
        self.client = Client()

    def test_search_courses_api(self):
        url = reverse('review:ajax_search_courses')
        response = self.client.get(url, {'term': 'CS'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 1)

    def test_get_professors_for_course_api(self):
        url = reverse('review:ajax_get_professors')
        params = {'course_id': self.course1.id}
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
        params = {'course_id': 999} # Use an ID that doesn't exist
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('professors', data)
        self.assertEqual(len(data['professors']), 0, "Should return an empty list for an invalid course ID.")

        