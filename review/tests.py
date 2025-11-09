import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

# Import models from your apps
from core.models import Course, Professor, Section, Campus, RoomMSTeam
from .models import Review

User = get_user_model()

class WriteReviewViewTestCase(TestCase):
    def setUp(self):
        """Set up non-modified objects used by all test methods."""
        self.user = User.objects.create_user(username='testuser', password='testpassword123')
        
        # Create all necessary related objects
        self.campus = Campus.objects.create(name='Test Campus')
        self.room = RoomMSTeam.objects.create(name='Test Room 101', campus=self.campus)
        self.course = Course.objects.create(code='CS331', name='Software Engineering')
        self.professor = Professor.objects.create(
            name='Dr. Test',
            campus=self.campus,
            description='A test professor.'
        )
        
        # --- จุดสำคัญ: สร้าง Section พร้อมกับ section_number ---
        self.section = Section.objects.create(
            course=self.course,
            section_number='701',  # <--- ต้องมีบรรทัดนี้
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

# ในคลาส WriteReviewViewTestCase

    def test_write_review_submission_successful(self):
        self.client.login(username='testuser', password='testpassword123')
        self.assertEqual(Review.objects.count(), 0)
        
        review_data = {
            'course': self.course.id,
            'section': '701', # User types this in
            'professor': self.professor.id,
            'rating': 5,
            'header': 'Great course!',
            'body': 'Learned a lot.',
            'incognito': False,
        }
        
        response = self.client.post(self.write_review_url, data=review_data)
        
        # --- แก้ไขตรงนี้ ---

        # 1. ตรวจสอบการ Redirect ก่อน เพราะเป็นสิ่งแรกที่ควรจะเกิดขึ้นหลังฟอร์ม valid
        self.assertRedirects(response, reverse('core:homepage'))

        # 2. ตรวจสอบว่ามี object ถูกสร้างขึ้นในฐานข้อมูลจริง
        self.assertEqual(Review.objects.count(), 1)

        # 3. (Optional) ตรวจสอบรายละเอียดของ object ที่สร้างขึ้น
        new_review = Review.objects.first()
        self.assertEqual(new_review.user, self.user)
        self.assertEqual(new_review.section, self.section)

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
            'section': '999', # Non-existent section
            'professor': self.professor.id,
            'rating': 4,
            'header': 'Wrong section',
            'body': 'Testing fake section.',
        }
        response = self.client.post(self.write_review_url, data=invalid_data)
        self.assertEqual(Review.objects.count(), 0)
        self.assertIn('__all__', response.context['form'].errors)


class ReviewAPIsTestCase(TestCase):
    # API tests are not relevant to this specific failure, but ensure they are correct too.
    def setUp(self):
        self.campus = Campus.objects.create(name='API Test Campus')
        self.room = RoomMSTeam.objects.create(name='API Room', campus=self.campus)
        self.course1 = Course.objects.create(code='CS101', name='Intro to CS')
        self.prof1 = Professor.objects.create(
            name='Prof. Turing',
            campus=self.campus,
            description='API test professor.'
        )
        self.sec1 = Section.objects.create(
            course=self.course1,
            section_number='01', # <--- ต้องมีบรรทัดนี้
            professor=self.prof1,
            campus=self.campus,
            room=self.room,
            date_time='Tue 13:00-15:00',
            location='CS Building'
        )
        self.client = Client()

    def test_search_courses_api(self):
        url = reverse('review:ajax_search_courses')
        response = self.client.get(url, {'term': 'CS'})
        self.assertEqual(response.status_code, 200)