from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import time
from core.models import Course, Section
from planner.models import SectionSchedule
from planner.utils import _time_to_slot_float, _time_to_slot_range
from planner.models import Planner
from django.core.exceptions import ValidationError

User = get_user_model()

class PlannerUtilsTests(TestCase):
    def test_time_conversion(self):
        self.assertEqual(_time_to_slot_float(time(8, 0)), 0.0)
        self.assertEqual(_time_to_slot_float(time(8, 30)), 1.0)
        
    def test_slot_range(self):
        slots = _time_to_slot_range(time(8, 0), time(9, 0))
        self.assertEqual(slots, {0, 1})
        slots = _time_to_slot_range(time(9, 0), time(8, 0))
        self.assertEqual(slots, set())

class PlannerModelTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        self.section = Section.objects.create(course=self.course, section_number="01")
    
    def test_schedule_validation(self):
        s = SectionSchedule(section=self.section, day_of_week=0, start_time=time(8,0), end_time=time(9,0))
        s.full_clean()
        s.save()
        
        s2 = SectionSchedule(section=self.section, day_of_week=0, start_time=time(9,0), end_time=time(8,0))
        with self.assertRaises(ValidationError):
            s2.full_clean()
            
        s3 = SectionSchedule(section=self.section, day_of_week=1, start_time=time(8,15), end_time=time(9,15))
        with self.assertRaises(ValidationError):
            s3.full_clean()
            
        s4 = SectionSchedule(section=self.section, day_of_week=0, start_time=time(8,30), end_time=time(9,30))
        with self.assertRaises(ValidationError):
            s4.full_clean()

class PlannerViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u', email='u@u.com', password='p')
        self.client.login(username='u', password='p')
        self.course = Course.objects.create(course_code="CS101", course_name="Intro", credit=3)
        self.section = Section.objects.create(course=self.course, section_number="01")
        self.schedule = SectionSchedule.objects.create(section=self.section, day_of_week=0, start_time=time(8,0), end_time=time(9,0))

    def test_planner_view(self):
        resp = self.client.get(reverse('planner:planner_view'))
        self.assertEqual(resp.status_code, 200)

    def test_add_remove_section(self):
        resp = self.client.get(reverse('planner:add_section', args=[self.section.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.user.planner.sections.filter(id=self.section.id).exists())
        
        resp = self.client.get(reverse('planner:remove_section', args=[self.section.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(self.user.planner.sections.filter(id=self.section.id).exists())

    def test_conflict_check(self):
        Planner.objects.create(user=self.user)
        self.user.planner.sections.add(self.section)
        sec2 = Section.objects.create(course=self.course, section_number="02")
        SectionSchedule.objects.create(section=sec2, day_of_week=0, start_time=time(8,30), end_time=time(9,30))
        
        resp = self.client.get(reverse('planner:add_section', args=[sec2.id]))
        self.assertEqual(resp.status_code, 400)
        
    def test_variants(self):
        resp = self.client.post(reverse('planner:create_variant'), {'name': 'Var1'})
        self.assertEqual(resp.status_code, 200)
        v_id = resp.json()['id']
        
        resp = self.client.get(reverse('planner:variant_add_section', args=[v_id, self.section.id]))
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.get(reverse('planner:list_variants'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['variants']), 1)
        
        resp = self.client.get(reverse('planner:variant_remove_section', args=[v_id, self.section.id]))
        self.assertEqual(resp.status_code, 200)
        
        # Add back for load test
        self.client.get(reverse('planner:variant_add_section', args=[v_id, self.section.id]))

        resp = self.client.post(reverse('planner:load_variant', args=[v_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(self.user.planner.sections.filter(id=self.section.id).exists())
        
        # Update course credit to meet minimum requirement (9 credits) for saving variant
        self.course.credit = 9
        self.course.save()
        resp = self.client.post(reverse('planner:save_current_variant'), {'name': 'Var2'})
        self.assertEqual(resp.status_code, 200)
        
        resp = self.client.post(reverse('planner:delete_variant', args=[v_id]))
        self.assertEqual(resp.status_code, 200)

    def test_add_schedule_manual(self):
        resp = self.client.post(reverse('planner:add_section_schedule'), {
            'section_id': self.section.id,
            'day': 1,
            'start_slot': 0,
            'span': 2
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(SectionSchedule.objects.filter(section=self.section, day_of_week=1).exists())

    def test_search_sections(self):
        resp = self.client.get(reverse('planner:search_sections'), {'q': 'CS101'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()['results']), 1)
