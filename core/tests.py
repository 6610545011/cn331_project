from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from review.models import Review
from core.models import Course, Prof, Section
from django.utils import timezone
from stats.models import DailyActiveUser, CourseSearchStat, CourseViewStat, CourseReviewStat
from datetime import date


class LatestReviewsAPITest(TestCase):
	def setUp(self):
		User = get_user_model()
		self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')
		self.client = Client()
		# Create Course / Prof / Section
		course = Course.objects.create(course_name='Test Course', course_code='TEST101', description='x', credit=3)
		prof = Prof.objects.create(prof_name='Dr Test')
		section = Section.objects.create(course=course, section_number='01')
		section.teachers.add(prof)
		from core.models import Enrollment
		Enrollment.objects.create(user=self.user, section=section)

		# create 12 reviews to ensure pagination (10 per page default)
		for i in range(12):
			Review.objects.create(user=self.user, course=course, section=section, prof=prof, head=f'Head {i}', body='Body', rating=4, date_created=timezone.now())

	def test_latest_reviews_api_pagination(self):
		url = reverse('core:latest_reviews_api')
		resp = self.client.get(url, {'page': 1})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIn('reviews_html', data)
		self.assertTrue(data['has_next'])
		self.assertEqual(data['next_page'], 2)

	def test_daily_active_user_middleware_creates_record(self):
		login = self.client.login(username='testuser', password='testpass')
		self.assertTrue(login)
		resp = self.client.get(reverse('core:homepage'))
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(DailyActiveUser.objects.filter(user=self.user, date=date.today()).exists())

	def test_course_search_stat_increments(self):
		# perform a search matching the course code to trigger increment
		url = reverse('core:search')
		resp = self.client.get(url, {'q': 'TEST101'})
		self.assertEqual(resp.status_code, 200)
		stat_exists = CourseSearchStat.objects.filter(course__course_code__iexact='TEST101', date=date.today()).exists()
		self.assertTrue(stat_exists)

	def test_course_view_stat_increments(self):
		# Call course detail page and expect view stat to increment
		url = reverse('core:course_detail', args=["TEST101"])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertTrue(CourseViewStat.objects.filter(course__course_code='TEST101', date=date.today()).exists())

	def test_write_review_increments_course_review_stat(self):
		# login and submit a review, then ensure CourseReviewStat increments
		login = self.client.login(username='testuser', password='testpass')
		self.assertTrue(login)
		course = Course.objects.get(course_code='TEST101')
		prof = Prof.objects.get(prof_name='Dr Test')
		url = reverse('review:write_review')
		data = {
			'course': str(course.id),
			'prof': str(prof.id),
			'header': 'Great course',
			'body': 'This class was helpful',
			'rating': '5',
		}
		resp = self.client.post(url, data)
		# Should redirect to homepage on success
		self.assertIn(resp.status_code, (302, 303))
		# Ensure review was created
		from review.models import Review
		self.assertTrue(Review.objects.filter(course=course, head='Great course', user=self.user).exists())
		# Then ensure stats incremented
		self.assertTrue(CourseReviewStat.objects.filter(course=course, date=date.today()).exists())



# Create your tests here.
