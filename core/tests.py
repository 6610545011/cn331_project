from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.urls import reverse

from core.models import Course, Prof, Campus, Section, Enrollment, TimeSlot, Teach
from review.models import Review

User = get_user_model()


class CoreModelsTestCase(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='student1', email='s1@example.com', password='pass')
		self.campus = Campus.objects.create(name='Main Campus')
		self.course = Course.objects.create(course_code='CS101', course_name='Intro to CS', description='Basics', credit=3)
		self.prof = Prof.objects.create(prof_name='Dr. Example', email='prof@example.com')
		self.timeslot = TimeSlot.objects.create(time='MWF 10:00-10:50')
		self.section = Section.objects.create(section_number='001', course=self.course, datetime='MWF 10:00', room='A101', campus=self.campus)
		# create Teach relationship
		Teach.objects.create(prof=self.prof, section=self.section)
		# enroll user
		Enrollment.objects.create(user=self.user, section=self.section)

	def test_str_methods(self):
		self.assertEqual(str(self.course), 'CS101 - Intro to CS')
		self.assertEqual(str(self.prof), 'Dr. Example')
		self.assertIn('Section 001', str(self.section))

	def test_all_professors_property(self):
		profs = self.course.all_professors
		self.assertIn(self.prof, profs)

	def test_enrollment_unique_constraint(self):
		# trying to create duplicate enrollment should raise IntegrityError
		from django.db import transaction
		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				Enrollment.objects.create(user=self.user, section=self.section)

	def test_section_timeslot_relation(self):
		# create a SectionTime via the timeslot m2m through model
		from core.models import SectionTime
		st = SectionTime.objects.create(section=self.section, slot=self.timeslot)
		self.assertIn(self.timeslot, self.section.schedule.all())

	def test_course_creation_with_all_fields(self):
		course = Course.objects.create(course_code='MA201', course_name='Calculus II', description='Advanced calculus', credit=4)
		self.assertEqual(course.credit, 4)
		self.assertEqual(course.course_code, 'MA201')

	def test_prof_optional_fields(self):
		prof_minimal = Prof.objects.create(prof_name='Dr. Min')
		self.assertIsNone(prof_minimal.email)
		self.assertIsNone(prof_minimal.imgurl)
		self.assertEqual(prof_minimal.description, '')

	def test_campus_unique_name(self):
		from django.db import transaction
		Campus.objects.create(name='Unique Campus')
		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				Campus.objects.create(name='Unique Campus')

	def test_teach_unique_constraint(self):
		from django.db import transaction
		prof2 = Prof.objects.create(prof_name='Dr. Two', email='two@example.com')
		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				Teach.objects.create(prof=self.prof, section=self.section)

	def test_section_cascade_delete_on_course(self):
		section_id = self.section.id
		self.course.delete()
		self.assertFalse(Section.objects.filter(id=section_id).exists())

	def test_enrollment_cascade_delete_on_user(self):
		enrollment_id = Enrollment.objects.first().id
		self.user.delete()
		self.assertFalse(Enrollment.objects.filter(id=enrollment_id).exists())

	def test_multiple_profs_for_same_course(self):
		prof2 = Prof.objects.create(prof_name='Dr. Second', email='prof2@example.com')
		section2 = Section.objects.create(section_number='002', course=self.course, campus=self.campus)
		Teach.objects.create(prof=prof2, section=section2)
		profs = self.course.all_professors.order_by('id')
		self.assertEqual(profs.count(), 2)

	def test_multiple_students_in_section(self):
		user2 = User.objects.create_user(username='student2', email='s2@example.com', password='pass')
		Enrollment.objects.create(user=user2, section=self.section)
		students = self.section.students.all()
		self.assertEqual(students.count(), 2)
		self.assertIn(self.user, students)
		self.assertIn(user2, students)

	def test_timeslot_str(self):
		self.assertEqual(str(self.timeslot), 'MWF 10:00-10:50')

	def test_teach_str(self):
		teach = Teach.objects.first()
		self.assertIn(self.prof.prof_name, str(teach))
		self.assertIn('001', str(teach))

	def test_enrollment_str(self):
		enrollment = Enrollment.objects.first()
		self.assertIn(self.user.email, str(enrollment))

	def test_sectiontime_str(self):
		from core.models import SectionTime
		st = SectionTime.objects.create(section=self.section, slot=self.timeslot)
		self.assertIn(self.timeslot.time, str(st))


class CoreViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='viewstudent', email='vs@example.com', password='pw')
        # authenticate the client as a real user to avoid SimpleLazyObject issues in queries
        self.client.force_login(self.user)
        self.campus = Campus.objects.create(name='View Campus')
        self.course = Course.objects.create(course_code='CS300', course_name='Databases', description='', credit=3)
        self.prof = Prof.objects.create(prof_name='Prof View', email='view@example.com')
        self.section = Section.objects.create(section_number='10', course=self.course, campus=self.campus)
        Teach.objects.create(prof=self.prof, section=self.section)
        self.review = Review.objects.create(user=self.user, course=self.course, section=self.section, prof=self.prof, head='Nice', body='Good class', rating=4)

    def test_homepage_renders(self):
        resp = self.client.get(reverse('core:homepage'))
        self.assertEqual(resp.status_code, 200)

    def test_search_view_context(self):
        resp = self.client.get(reverse('core:search'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('results', resp.context)
        self.assertIn('courses', resp.context)

    def test_prof_detail_view(self):
        resp = self.client.get(reverse('core:professor_detail', args=[self.prof.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['prof'].id, self.prof.id)
        self.assertIn('reviews', resp.context)

    def test_course_detail_view(self):
        resp = self.client.get(reverse('core:course_detail', args=[self.course.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['course'].id, self.course.id)
        self.assertIn('reviews', resp.context)

    def test_search_view_with_query(self):
        resp = self.client.get(reverse('core:search'), {'q': 'Data'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Databases', str(resp.context['courses']))

    def test_search_view_sorting_alphabetical(self):
        resp = self.client.get(reverse('core:search'), {'sort_by': 'alphabetical', 'order': 'asc'})
        self.assertEqual(resp.status_code, 200)

    def test_prof_detail_nonexistent(self):
        resp = self.client.get(reverse('core:professor_detail', args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_course_detail_nonexistent(self):
        resp = self.client.get(reverse('core:course_detail', args=[9999]))
        self.assertEqual(resp.status_code, 404)

    def test_about_view(self):
        resp = self.client.get(reverse('core:about'))
        self.assertEqual(resp.status_code, 200)

