import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Course, Professor, Section, Campus, RoomMSTeam
from .models import Review

User = get_user_model()

class WriteReviewViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword123')
        
        self.campus = Campus.objects.create(name='Test Campus')
        self.room = RoomMSTeam.objects.create(name='Test Room 101', campus=self.campus)
        self.course = Course.objects.create(code='CS331', name='Software Engineering')
        
        # --- แก้ไขตรงนี้: เพิ่ม room ตอนสร้าง Professor ---
        self.professor = Professor.objects.create(
            name='Dr. Test',
            campus=self.campus,
            room=self.room,  # <--- เพิ่มบรรทัดนี้
            description='A test professor.'
        )
        
        # --- แก้ไขตรงนี้: เปลี่ยน section_number เป็น number ---
        self.section = Section.objects.create(
            course=self.course,
            section_number='701',  # <--- แก้ไขชื่อฟิลด์
            professor=self.professor,
            campus=self.campus,
            room=self.room,
            date_time='Mon 10:00-12:00',
            location='Main Building'
        )
        
        self.client = Client()
        self.write_review_url = reverse('review:write_review')

    # ... (โค้ดเทสต์เคสอื่นๆ เหมือนเดิม) ...
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


class ReviewAPIsTestCase(TestCase):
    def setUp(self):
        self.campus = Campus.objects.create(name='API Test Campus')
        self.room = RoomMSTeam.objects.create(name='API Room', campus=self.campus)
        self.course1 = Course.objects.create(code='CS101', name='Intro to CS')
        
        # --- แก้ไขตรงนี้: เพิ่ม room ตอนสร้าง Professor ---
        self.prof1 = Professor.objects.create(
            name='Prof. Turing',
            campus=self.campus,
            room=self.room, # <--- เพิ่มบรรทัดนี้
            description='API test professor.'
        )

        # --- แก้ไขตรงนี้: เปลี่ยน section_number เป็น number ---
        self.sec1 = Section.objects.create(
            course=self.course1,
            section_number='01', # <--- แก้ไขชื่อฟิลด์
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
    