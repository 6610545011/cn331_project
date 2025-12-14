from django.test import TestCase
from django.utils import timezone
from datetime import date
from stats.models import DailyActiveUser, CourseSearchStat, CourseViewStat, CourseReviewStat
from core.models import Course
from django.contrib.auth import get_user_model

User = get_user_model()


class StatsModelsTests(TestCase):
    def test_dau_str(self):
        user = User.objects.create_user(username='dau', email='dau@example.com', password='pw')
        dau = DailyActiveUser.objects.create(user=user, date=date.today())
        self.assertIn('Active', str(dau))

    def test_course_search_stat_str(self):
        course = Course.objects.create(course_code='STS1', course_name='Stats1', credit=1)
        stat = CourseSearchStat.objects.create(course=course, date=date.today(), count=5)
        self.assertIn('STS1', str(stat))
        self.assertIn('searches', str(stat))

    def test_course_view_stat_str(self):
        course = Course.objects.create(course_code='STS2', course_name='Stats2', credit=1)
        stat = CourseViewStat.objects.create(course=course, date=date.today(), count=3)
        self.assertIn('STS2', str(stat))
        self.assertIn('views', str(stat))

    def test_course_review_stat_str(self):
        course = Course.objects.create(course_code='STS3', course_name='Stats3', credit=1)
        stat = CourseReviewStat.objects.create(course=course, date=date.today(), count=2)
        self.assertIn('STS3', str(stat))
        self.assertIn('reviews', str(stat))
