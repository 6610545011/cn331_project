from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import time
from core.models import Course, Section
from planner.models import SectionSchedule, Planner, PlanVariant
from planner.utils import _time_to_slot_float, _time_to_slot_range
from planner.views import _pastel_color_for_key
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


class PlannerViewEdgeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='edge', email='edge@example.com', password='pw')
        self.client.login(username='edge', password='pw')
        self.course = Course.objects.create(course_code="EDGE1", course_name="Edge", credit=1)
        self.section = Section.objects.create(course=self.course, section_number="01")
        SectionSchedule.objects.create(section=self.section, day_of_week=0, start_time=time(8,0), end_time=time(9,0))

    def test_add_section_to_planner_conflict(self):
        planner, _ = Planner.objects.get_or_create(user=self.user)
        planner.sections.add(self.section)

        other_course = Course.objects.create(course_code="EDGE2", course_name="Other", credit=1)
        other_sec = Section.objects.create(course=other_course, section_number="02")
        SectionSchedule.objects.create(section=other_sec, day_of_week=0, start_time=time(8,30), end_time=time(9,30))

        resp = self.client.get(reverse('planner:add_section', args=[other_sec.id]))
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])

    def test_add_section_to_planner_warning_low_credit(self):
        resp = self.client.get(reverse('planner:add_section', args=[self.section.id]))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['ok'])
        self.assertIn('warning', data)
        self.assertIn('Total credits', data['warning'])

    def test_remove_section_without_planner(self):
        user = User.objects.create_user(username='noplan', email='no@plan.com', password='pw')
        self.client.logout()
        self.client.login(username='noplan', password='pw')
        resp = self.client.get(reverse('planner:remove_section', args=[self.section.id]))
        self.assertEqual(resp.status_code, 404)
        self.assertFalse(resp.json()['ok'])

    def test_add_section_schedule_errors(self):
        self.client.logout()
        self.client.login(username='edge', password='pw')

        resp = self.client.get(reverse('planner:add_section_schedule'))
        self.assertEqual(resp.status_code, 405)

        resp = self.client.post(reverse('planner:add_section_schedule'), {'section_id': self.section.id})
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(reverse('planner:add_section_schedule'), {
            'section_id': 9999,
            'day': 0,
            'start_slot': 0,
            'span': 1
        })
        self.assertEqual(resp.status_code, 404)

        resp = self.client.post(reverse('planner:add_section_schedule'), {
            'section_id': self.section.id,
            'day': 'x',
            'start_slot': 'bad',
            'span': 'y'
        })
        self.assertEqual(resp.status_code, 400)

        resp = self.client.post(reverse('planner:add_section_schedule'), {
            'section_id': self.section.id,
            'day': 0,
            'start_slot': 24,
            'span': 1
        })
        self.assertEqual(resp.status_code, 400)

    def test_color_generation_stable(self):
        color = _pastel_color_for_key('demo-key')
        self.assertTrue(color.startswith('hsl('))
        # Deterministic: same key yields same color
        self.assertEqual(color, _pastel_color_for_key('demo-key'))

    def test_create_variant_validation(self):
        resp = self.client.get(reverse('planner:create_variant'))
        self.assertEqual(resp.status_code, 405)

        resp = self.client.post(reverse('planner:create_variant'), {})
        self.assertEqual(resp.status_code, 400)

    def test_save_current_variant_credit_bounds(self):
        planner, _ = Planner.objects.get_or_create(user=self.user)
        planner.sections.add(self.section)

        resp = self.client.post(reverse('planner:save_current_variant'), {'name': 'TooLow'})
        self.assertEqual(resp.status_code, 400)
        self.assertIn('between 9 and 22', resp.json()['error'])

    def test_variant_conflict_and_load_method(self):
        planner, _ = Planner.objects.get_or_create(user=self.user)
        planner.sections.add(self.section)
        variant = PlanVariant.objects.create(planner=planner, name='Base')
        variant.sections.add(self.section)

        conflict_course = Course.objects.create(course_code='VCF', course_name='Conflict', credit=3)
        conflict_section = Section.objects.create(course=conflict_course, section_number='01')
        SectionSchedule.objects.create(section=conflict_section, day_of_week=0, start_time=time(8,30), end_time=time(9,30))

        resp = self.client.get(reverse('planner:load_variant', args=[variant.id]))
        self.assertEqual(resp.status_code, 405)

        resp = self.client.get(reverse('planner:variant_add_section', args=[variant.id, conflict_section.id]))
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['ok'])
