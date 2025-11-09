import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Import models from your apps
# You might need to adjust the import path based on your project structure
from core.models import Course, Professor, Section
from .models import Review

# Get the custom User model if you have one, otherwise the default User
User = get_user_model()

class ReviewViewsTestCase(TestCase):
    """
    Test suite for the main review views like the write_review form.
    """
    def setUp(self):
        """
        Set up non-modified objects used by all test methods.
        This method is run before each test.
        """
        # 1. Create a test user
        self.user = User.objects.create_user(username='testuser', password='testpassword123')

        # 2. Create related objects for the review form
        self.course = Course.objects.create(code='CS101', name='Introduction to Computer Science')
        self.professor = Professor.objects.create(name='Dr. Ada Lovelace')
        self.section = Section.objects.create(
            course=self.course,
            section_number='780001',
            professor=self.professor
        )

        # 3. Instantiate a client to make requests
        self.client = Client()

        # 4. Define URLs for convenience
        self.write_review_url = reverse('review:write_review')

    def test_write_review_page_redirects_if_not_logged_in(self):
        """
        Test that the write_review page redirects anonymous users to the login page.
        """
        response = self.client.get(self.write_review_url)
        self.assertEqual(response.status_code, 302) # 302 is a redirect
        self.assertRedirects(response, f'/users/login/?next={self.write_review_url}')

    def test_write_review_page_loads_for_logged_in_user(self):
        """
        Test that the write_review page loads correctly (GET request) for a logged-in user.
        """
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(self.write_review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'review/write_review.html')
        self.assertIn('form', response.context)

    def test_write_review_submission_successful(self):
        """
        Test that a valid POST request creates a new Review object in the database.
        """
        self.client.login(username='testuser', password='testpassword123')
        
        # Check that there are no reviews initially
        self.assertEqual(Review.objects.count(), 0)

        review_data = {
            'course': self.course.id,
            'section': self.section.id,
            'professor': self.professor.id,
            'rating': 5,
            'header': 'Excellent Course!',
            'body': 'This was a fantastic introduction to the subject.',
            'incognito': False,
        }

        response = self.client.post(self.write_review_url, data=review_data)

        # Check that a new review was created
        self.assertEqual(Review.objects.count(), 1)
        
        # Check the details of the created review
        new_review = Review.objects.first()
        self.assertEqual(new_review.user, self.user)
        self.assertEqual(new_review.rating, 5)
        self.assertEqual(new_review.header, 'Excellent Course!')
        
        # Check that it redirects to the homepage after successful submission
        self.assertRedirects(response, reverse('core:homepage'))

    def test_write_review_submission_invalid(self):
        """
        Test that an invalid POST request does not create a review and re-renders the form.
        """
        self.client.login(username='testuser', password='testpassword123')
        
        # Data is invalid because 'rating' is missing
        invalid_review_data = {
            'course': self.course.id,
            'header': 'Incomplete Review',
            'body': 'I forgot to add a rating.',
        }

        response = self.client.post(self.write_review_url, data=invalid_review_data)

        # Check that no review was created
        self.assertEqual(Review.objects.count(), 0)
        
        # Check that the page re-renders with the form (not a redirect)
        self.assertEqual(response.status_code, 200)
        
        # Check that the form contains errors
        self.assertTrue(response.context['form'].errors)


class ReviewAPIsTestCase(TestCase):
    """
    Test suite for the API views that return JSON data.
    """
    def setUp(self):
        self.course1 = Course.objects.create(code='CS101', name='Intro to CS')
        self.course2 = Course.objects.create(code='MA202', name='Calculus II')
        self.prof1 = Professor.objects.create(name='Prof. Turing')
        self.sec1 = Section.objects.create(course=self.course1, section_number='01', professor=self.prof1)
        self.client = Client()

    def test_search_courses_api(self):
        """
        Test the course search API endpoint.
        """
        url = reverse('review:ajax_search_courses')
        response = self.client.get(url, {'term': 'CS'})
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data['results']), 1)
        self.assertEqual(data['results'][0]['id'], self.course1.id)
        self.assertEqual(data['results'][0]['text'], f"{self.course1.code} - {self.course1.name}")

    def test_get_sections_for_course_api(self):
        """
        Test the API that fetches sections for a given course.
        """
        url = reverse('review:ajax_get_sections')
        response = self.client.get(url, {'course_id': self.course1.id})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data['sections']), 1)
        self.assertEqual(data['sections'][0]['id'], self.sec1.id)
        self.assertEqual(data['sections'][0]['text'], f"Section {self.sec1.section_number}")

    def test_get_professors_for_course_api(self):
        """
        Test the API that fetches professors for a given course.
        """
        url = reverse('review:ajax_get_professors')
        response = self.client.get(url, {'course_id': self.course1.id})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(len(data['professors']), 1)
        self.assertEqual(data['professors'][0]['id'], self.prof1.id)
        self.assertEqual(data['professors'][0]['name'], self.prof1.name)