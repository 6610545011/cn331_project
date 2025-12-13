from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from review.models import Review, Bookmark, ReviewUpvote
from core.models import Course, Prof, Section
from django.utils import timezone
from stats.models import DailyActiveUser, CourseSearchStat, CourseViewStat, CourseReviewStat
from datetime import date
from core.converters import CaseInsensitiveSlugConverter
from core.templatetags.core_extras import unicode_slugify


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

	def test_latest_reviews_api_empty_page(self):
		url = reverse('core:latest_reviews_api')
		resp = self.client.get(url, {'page': 999})
		self.assertEqual(resp.status_code, 200)
		self.assertFalse(resp.json()['has_next'])

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


class CoreViewsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='coreuser', email='core@example.com', password='password')
        self.client = Client()
        
    def test_converter(self):
        c = CaseInsensitiveSlugConverter()
        self.assertEqual(c.to_python("ABC"), "ABC")
        self.assertEqual(c.to_url("ABC"), "ABC")
        self.assertEqual(c.regex, "[^/]+")

    def test_about(self):
        resp = self.client.get(reverse('core:about'))
        self.assertEqual(resp.status_code, 200)

    def test_search_filters(self):
        c = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        p = Prof.objects.create(prof_name="Dr. Smith")
        s = Section.objects.create(course=c, section_number="01")
        s.teachers.add(p)
        
        resp = self.client.get(reverse('core:search'), {'q': 'CS101', 'sort_by': 'alphabetical', 'order': 'desc'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CS101")
        
        resp = self.client.get(reverse('core:search'))
        self.assertEqual(resp.status_code, 200)

    def test_prof_detail(self):
        p = Prof.objects.create(prof_name="Dr. Smith")
        resp = self.client.get(reverse('core:professor_detail', args=[p.id]))
        self.assertEqual(resp.status_code, 200)

    def test_toggle_bookmark(self):
        self.client.login(username='coreuser', password='password')
        c = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        
        resp = self.client.post(reverse('core:toggle_course_bookmark', args=[c.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()['bookmarked'])

    def test_homepage_authenticated(self):
        self.client.login(username='coreuser', password='password')
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)

    def test_course_detail_authenticated(self):
        self.client.login(username='coreuser', password='password')
        c = Course.objects.create(course_code="CS102", course_name="Intro 2", credit=3)
        resp = self.client.get(reverse('core:course_detail', args=[c.course_code]))
        self.assertEqual(resp.status_code, 200)

    def test_prof_detail_authenticated(self):
        self.client.login(username='coreuser', password='password')
        p = Prof.objects.create(prof_name="Dr. Jones")
        resp = self.client.get(reverse('core:professor_detail', args=[p.id]))
        self.assertEqual(resp.status_code, 200)

    def test_homepage_pagination_out_of_range(self):
        resp = self.client.get(reverse('core:homepage'), {'page': 999})
        self.assertEqual(resp.status_code, 200)

    def test_search_sorting_lambda(self):
        p = Prof.objects.create(prof_name="Albert")
        c = Course.objects.create(course_code="BIO101", course_name="Biology", credit=3)
        s = Section.objects.create(course=c, section_number="01")
        r = Review.objects.create(user=self.user, course=c, head="Zebra", body="x", rating=5)
        
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'asc'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(len(resp.context['results']) >= 4)

    def test_homepage_unauthenticated(self):
        self.client.logout()
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)

    def test_latest_reviews_api_unauthenticated(self):
        self.client.logout()
        url = reverse('core:latest_reviews_api')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_search_no_query(self):
        resp = self.client.get(reverse('core:search'))
        self.assertEqual(resp.status_code, 200)

    def test_prof_detail_unauthenticated(self):
        self.client.logout()
        p = Prof.objects.create(prof_name="Dr. Who")
        resp = self.client.get(reverse('core:professor_detail', args=[p.id]))
        self.assertEqual(resp.status_code, 200)

    def test_course_detail_unauthenticated(self):
        self.client.logout()
        c = Course.objects.create(course_code="CS_UNAUTH", course_name="Test Unauth", credit=3)
        resp = self.client.get(reverse('core:course_detail', args=[c.course_code]))
        self.assertEqual(resp.status_code, 200)

    def test_toggle_bookmark_remove(self):
        self.client.login(username='coreuser', password='password')
        c = Course.objects.create(course_code="CS_BM", course_name="Test BM", credit=3)
        # Add
        resp = self.client.post(reverse('core:toggle_course_bookmark', args=[c.id]))
        self.assertTrue(resp.json()['bookmarked'])
        # Remove
        resp = self.client.post(reverse('core:toggle_course_bookmark', args=[c.id]))
        self.assertFalse(resp.json()['bookmarked'])

    def test_search_matches_all_types(self):
        # Create entities that match "Common"
        p = Prof.objects.create(prof_name="Common Prof")
        c = Course.objects.create(course_code="COM101", course_name="Common Course", credit=3)
        s = Section.objects.create(course=c, section_number="01")
        # Section matches via course name "Common Course"
        
        # Review matches via head
        r = Review.objects.create(user=self.user, course=c, head="Common Review", body="x", rating=5)
        
        resp = self.client.get(reverse('core:search'), {'q': 'Common'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(p, resp.context['professors'])
        self.assertIn(c, resp.context['courses'])
        self.assertIn(s, resp.context['sections'])
        self.assertIn(r, resp.context['reviews'])

    def test_search_order_desc(self):
        p1 = Prof.objects.create(prof_name="Alpha")
        p2 = Prof.objects.create(prof_name="Beta")
        
        resp = self.client.get(reverse('core:search'), {'q': '', 'sort_by': 'alphabetical', 'order': 'desc'})
        self.assertEqual(resp.status_code, 200)
        results = resp.context['professors']
        self.assertEqual(list(results), [p2, p1])

    def test_stats_update_existing(self):
        # Create existing stats
        c = Course.objects.create(course_code="STAT101", course_name="Stats", credit=3)
        today = date.today()
        CourseViewStat.objects.create(course=c, date=today, count=1)
        CourseSearchStat.objects.create(course=c, date=today, count=1)
        
        # Trigger update via view
        self.client.get(reverse('core:course_detail', args=[c.course_code]))
        self.assertEqual(CourseViewStat.objects.get(course=c, date=today).count, 2)
        
        # Trigger search update
        self.client.get(reverse('core:search'), {'q': 'STAT101'})
        self.assertEqual(CourseSearchStat.objects.get(course=c, date=today).count, 2)

    def test_search_section_by_teacher(self):
        c = Course.objects.create(course_code="SEC101", course_name="Sec", credit=3)
        p = Prof.objects.create(prof_name="TeacherName")
        s = Section.objects.create(course=c, section_number="99")
        s.teachers.add(p)
        
        resp = self.client.get(reverse('core:search'), {'q': 'TeacherName'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(s, resp.context['sections'])

    def test_course_detail_404(self):
        resp = self.client.get(reverse('core:course_detail', args=['NONEXISTENT']))
        self.assertEqual(resp.status_code, 404)

    def test_search_mixed_sorting(self):
        # Create items
        p = Prof.objects.create(prof_name="A_Prof")
        c = Course.objects.create(course_code="B_Course", course_name="B_Course", credit=1)
        # Section str: "B_Course Section 01"
        s = Section.objects.create(course=c, section_number="01")
        r = Review.objects.create(user=self.user, course=c, head="D_Review", body="x", rating=5)
        
        # Search all (empty q)
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'asc'})
        results = resp.context['results']
        
        # Expected order: A_Prof, B_Course, Section (str starts with B_Course...), D_Review
        self.assertEqual(results[0], p)
        self.assertEqual(results[1], c)
        self.assertEqual(results[2], s)
        self.assertEqual(results[3], r)

class CoreExtrasTests(TestCase):
    def test_unicode_slugify(self):
        self.assertEqual(unicode_slugify("Hello World"), "hello-world")
        self.assertEqual(unicode_slugify("สวัสดี"), "สวัสดี")


class CoreViewsCoverageTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='covuser', email='cov@example.com', password='password')
        self.client = Client()
        self.client.login(username='covuser', password='password')
        
        self.course = Course.objects.create(course_code="COV101", course_name="Coverage Course", credit=3)
        self.prof = Prof.objects.create(prof_name="Prof Coverage")
        self.section = Section.objects.create(course=self.course, section_number="01")
        self.section.teachers.add(self.prof)
        
        self.review = Review.objects.create(
            user=self.user, 
            course=self.course, 
            prof=self.prof, 
            section=self.section,
            head="Coverage Review", 
            body="Body", 
            rating=5
        )

    def test_homepage_annotations(self):
        # Setup: Bookmark and Vote
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        ReviewUpvote.objects.create(user=self.user, review=self.review, vote_type=1)
        
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)
        
        # Find the review in context
        reviews = resp.context['reviews']
        target_review = next((r for r in reviews if r.id == self.review.id), None)
        self.assertIsNotNone(target_review)
        
        # Check annotations
        self.assertTrue(target_review.is_bookmarked)
        self.assertEqual(target_review.user_vote, 1)
        self.assertEqual(target_review.score, 1)

    def test_course_detail_context(self):
        # Setup: Bookmark Course (review=None)
        Bookmark.objects.create(user=self.user, course=self.course, review=None)
        # Also bookmark the review
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        
        resp = self.client.get(reverse('core:course_detail', args=[self.course.course_code]))
        self.assertEqual(resp.status_code, 200)
        
        self.assertTrue(resp.context['course_is_bookmarked'])
        
        reviews = resp.context['reviews']
        target_review = next((r for r in reviews if r.id == self.review.id), None)
        self.assertTrue(target_review.is_bookmarked)

    def test_prof_detail_context(self):
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        
        resp = self.client.get(reverse('core:professor_detail', args=[self.prof.id]))
        self.assertEqual(resp.status_code, 200)
        
        reviews = resp.context['reviews']
        target_review = next((r for r in reviews if r.id == self.review.id), None)
        self.assertTrue(target_review.is_bookmarked)

    def test_search_annotations(self):
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        
        resp = self.client.get(reverse('core:search'), {'q': 'Coverage'})
        self.assertEqual(resp.status_code, 200)
        
        reviews = resp.context['reviews']
        target_review = next((r for r in reviews if r.id == self.review.id), None)
        self.assertIsNotNone(target_review)
        self.assertTrue(target_review.is_bookmarked)

    def test_toggle_course_bookmark_failures(self):
        # GET request (should be 405)
        resp = self.client.get(reverse('core:toggle_course_bookmark', args=[self.course.id]))
        self.assertEqual(resp.status_code, 405)
        
        # Invalid Course ID (should be 404)
        resp = self.client.post(reverse('core:toggle_course_bookmark', args=[99999]))
        self.assertEqual(resp.status_code, 404)
        
        # Unauthenticated
        self.client.logout()
        resp = self.client.post(reverse('core:toggle_course_bookmark', args=[self.course.id]))
        self.assertEqual(resp.status_code, 302)

    def test_prof_detail_404(self):
        resp = self.client.get(reverse('core:professor_detail', args=[99999]))
        self.assertEqual(resp.status_code, 404)

    def test_latest_reviews_api_content(self):
        Bookmark.objects.create(user=self.user, review=self.review, course=self.course)
        
        url = reverse('core:latest_reviews_api')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Check for active bookmark class in HTML
        self.assertIn('bookmark-btn active', data['reviews_html'])


class CoreViewsExtendedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='ext', password='password')
        
    def test_search_by_descriptions_and_body(self):
        p = Prof.objects.create(prof_name="P1", description="HiddenProfDesc")
        c = Course.objects.create(course_code="C1", course_name="C1", credit=1, description="HiddenCourseDesc")
        r = Review.objects.create(user=self.user, course=c, head="H1", body="HiddenReviewBody", rating=5)
        
        # Search Prof Description
        resp = self.client.get(reverse('core:search'), {'q': 'HiddenProfDesc'})
        self.assertIn(p, resp.context['professors'])
        
        # Search Course Description
        resp = self.client.get(reverse('core:search'), {'q': 'HiddenCourseDesc'})
        self.assertIn(c, resp.context['courses'])
        
        # Search Review Body
        resp = self.client.get(reverse('core:search'), {'q': 'HiddenReviewBody'})
        self.assertIn(r, resp.context['reviews'])

    def test_search_analytics_limit(self):
        # Create 6 courses matching "LimitTest"
        for i in range(6):
            Course.objects.create(course_code=f"LIMIT{i}", course_name=f"LimitTest {i}", credit=1)
            
        self.client.get(reverse('core:search'), {'q': 'LimitTest'})
        
        today = date.today()
        count = CourseSearchStat.objects.filter(date=today, course__course_name__contains="LimitTest").count()
        self.assertEqual(count, 5)

    def test_latest_reviews_api_params(self):
        # Test page_size
        c = Course.objects.create(course_code="API", course_name="API", credit=1)
        for i in range(5):
            Review.objects.create(user=self.user, course=c, head=f"R{i}", body="x", rating=5)
            
        url = reverse('core:latest_reviews_api')
        resp = self.client.get(url, {'page_size': 2})
        data = resp.json()
        self.assertTrue(data['has_next'])
        self.assertEqual(data['next_page'], 2)

    def test_search_unknown_sort(self):
        resp = self.client.get(reverse('core:search'), {'sort_by': 'unknown_sort_method'})
        self.assertEqual(resp.status_code, 200)

    def test_course_detail_case_insensitive(self):
        c = Course.objects.create(course_code="CASE101", course_name="Case", credit=1)
        resp = self.client.get(reverse('core:course_detail', args=['case101']))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['course'], c)

    def test_search_section_sorting(self):
        c = Course.objects.create(course_code="C", course_name="C", credit=1)
        s1 = Section.objects.create(course=c, section_number="01")
        s2 = Section.objects.create(course=c, section_number="02")
        
        # Ascending
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'asc'})
        results = [x for x in resp.context['results'] if isinstance(x, Section)]
        self.assertEqual(results, [s1, s2])
        
        # Descending
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'desc'})
        results = [x for x in resp.context['results'] if isinstance(x, Section)]
        self.assertEqual(results, [s2, s1])


class CoreViewsFinalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='final', password='password')
        self.client.login(username='final', password='password')

    def test_search_result_ordering_mixed_types(self):
        # Create items that will be sorted by name/head/str
        p = Prof.objects.create(prof_name="Aaron")
        c = Course.objects.create(course_code="B1", course_name="Baron", credit=1)
        r = Review.objects.create(user=self.user, course=c, head="Caron", body="x", rating=5)
        # Section: "Daron" (via course name)
        c2 = Course.objects.create(course_code="D1", course_name="Daron", credit=1)
        s = Section.objects.create(course=c2, section_number="01")
        
        # Search empty q to get all
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'asc'})
        results = resp.context['results']
        
        # Filter to our created objects
        results = [x for x in results if x in [p, c, r, s]]
        
        self.assertEqual(results[0], p) # Aaron
        self.assertEqual(results[1], c) # Baron
        self.assertEqual(results[2], r) # Caron
        self.assertEqual(results[3], s) # Daron (D1 - Daron Section 01)
        
        # Descending
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'desc'})
        results = resp.context['results']
        results = [x for x in results if x in [p, c, r, s]]
        self.assertEqual(results[0], s)
        self.assertEqual(results[1], r)
        self.assertEqual(results[2], c)
        self.assertEqual(results[3], p)

    def test_latest_reviews_api_invalid_params(self):
        # Should raise ValueError internally, resulting in 500
        with self.assertRaises(ValueError):
            self.client.get(reverse('core:latest_reviews_api'), {'page': 'invalid'})
            
        with self.assertRaises(ValueError):
            self.client.get(reverse('core:latest_reviews_api'), {'page_size': 'invalid'})

    def test_review_annotations_no_votes(self):
        c = Course.objects.create(course_code="NOVOTE", course_name="No Vote", credit=1)
        r = Review.objects.create(user=self.user, course=c, head="No Vote Review", body="x", rating=5)
        
        resp = self.client.get(reverse('core:homepage'))
        reviews = resp.context['reviews']
        target = next(x for x in reviews if x.id == r.id)
        
        self.assertEqual(target.score, 0)
        self.assertEqual(target.user_vote, 0)


class CoreViewsMoreCoverageTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='more', password='password')
        self.client.login(username='more', password='password')
        self.course = Course.objects.create(course_code="MORE101", course_name="More Tests", credit=3)
        self.prof = Prof.objects.create(prof_name="Prof More")
        self.section = Section.objects.create(course=self.course, section_number="01")
        self.section.teachers.add(self.prof)
        self.review = Review.objects.create(user=self.user, course=self.course, prof=self.prof, section=self.section, head="Rev", body="Body", rating=5)

    def test_search_query_present_no_courses(self):
        # Search for something that matches a Prof but not a Course
        # This ensures 'query' is True, but 'courses.exists()' is False
        # So analytics block should be skipped
        initial_count = CourseSearchStat.objects.count()
        resp = self.client.get(reverse('core:search'), {'q': 'Prof More'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.prof, resp.context['professors'])
        self.assertEqual(CourseSearchStat.objects.count(), initial_count)

    def test_search_section_by_course_code(self):
        # Search by course code "MORE101"
        resp = self.client.get(reverse('core:search'), {'q': 'MORE101'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.section, resp.context['sections'])

    def test_course_detail_bookmark_inheritance(self):
        # Bookmark the course only
        Bookmark.objects.create(user=self.user, course=self.course, review=None)
        
        resp = self.client.get(reverse('core:course_detail', args=[self.course.course_code]))
        reviews = resp.context['reviews']
        target = next(r for r in reviews if r.id == self.review.id)
        
        # Logic in view: Q(review=OuterRef('pk')) | Q(review=None)
        # Should be True
        self.assertTrue(target.is_bookmarked)

    def test_prof_detail_bookmark_no_inheritance(self):
        # Bookmark the course only
        Bookmark.objects.create(user=self.user, course=self.course, review=None)
        
        resp = self.client.get(reverse('core:professor_detail', args=[self.prof.id]))
        reviews = resp.context['reviews']
        target = next(r for r in reviews if r.id == self.review.id)
        
        # Logic in view: review=OuterRef('pk') only
        # Should be False
        self.assertFalse(target.is_bookmarked)

    def test_search_order_invalid(self):
        p1 = Prof.objects.create(prof_name="Alpha")
        p2 = Prof.objects.create(prof_name="Beta")
        
        # order='invalid' should default to asc
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'invalid'})
        results = list(resp.context['professors'])
        # Filter to just these two
        results = [p for p in results if p in [p1, p2]]
        self.assertEqual(results, [p1, p2])


class CoreViewsSearchBranchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='branch', password='password')
        
    def test_search_course_name_match(self):
        c = Course.objects.create(course_code="X", course_name="UniqueCourseName", credit=1)
        resp = self.client.get(reverse('core:search'), {'q': 'UniqueCourseName'})
        self.assertIn(c, resp.context['courses'])

    def test_search_review_head_match(self):
        c = Course.objects.create(course_code="X", course_name="X", credit=1)
        r = Review.objects.create(user=self.user, course=c, head="UniqueReviewHead", body="body", rating=5)
        resp = self.client.get(reverse('core:search'), {'q': 'UniqueReviewHead'})
        self.assertIn(r, resp.context['reviews'])

    def test_search_section_course_name_match(self):
        c = Course.objects.create(course_code="X", course_name="UniqueSectionCourseName", credit=1)
        s = Section.objects.create(course=c, section_number="01")
        resp = self.client.get(reverse('core:search'), {'q': 'UniqueSectionCourseName'})
        self.assertIn(s, resp.context['sections'])
        
    def test_latest_reviews_api_last_page(self):
        c = Course.objects.create(course_code="API2", course_name="API2", credit=1)
        Review.objects.create(user=self.user, course=c, head="R1", body="x", rating=5)
        url = reverse('core:latest_reviews_api')
        resp = self.client.get(url, {'page': 1, 'page_size': 5})
        data = resp.json()
        self.assertFalse(data['has_next'])
        self.assertIsNone(data['next_page'])
