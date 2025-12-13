from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from datetime import timedelta


class SectionSchedule(models.Model):
	"""Structured time entries for a single `core.Section`.

	A Section can have multiple SectionSchedule rows (e.g., Mon & Wed meetings).
	day_of_week: 0=Monday .. 6=Sunday
	"""
	DAY_CHOICES = [
		(0, 'Mon'),
		(1, 'Tue'),
		(2, 'Wed'),
		(3, 'Thu'),
		(4, 'Fri'),
		(5, 'Sat'),
		(6, 'Sun'),
	]

	section = models.ForeignKey('core.Section', on_delete=models.CASCADE, related_name='schedules')
	day_of_week = models.IntegerField(choices=DAY_CHOICES)
	start_time = models.TimeField()
	end_time = models.TimeField()

	class Meta:
		verbose_name = 'Section Schedule'
		verbose_name_plural = 'Section Schedules'

	def __str__(self):
		return f"{self.section} {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

	def clean(self):
		# Basic validations: end_time > start_time
		if self.end_time <= self.start_time:
			raise ValidationError('end_time must be after start_time')

		# Ensure times align with 30-minute slots based on SLOT_START/SLOT_DURATION
		from .utils import SLOT_START, SLOT_DURATION_MINUTES
		# compute minutes since slot start
		def minutes_since_start(t):
			return (t.hour * 60 + t.minute) - (SLOT_START.hour * 60 + SLOT_START.minute)

		start_min = minutes_since_start(self.start_time)
		end_min = minutes_since_start(self.end_time)

		if start_min < 0 or end_min <= 0:
			raise ValidationError('Times must be within planner supported hours')

		if start_min % SLOT_DURATION_MINUTES != 0 or end_min % SLOT_DURATION_MINUTES != 0:
			raise ValidationError('Start and end times must align to 30-minute slots')

		# Prevent overlapping schedules for the same section on same day
		overlaps = SectionSchedule.objects.filter(section=self.section, day_of_week=self.day_of_week).exclude(pk=self.pk)
		for o in overlaps:
			# if intervals overlap
			if not (self.end_time <= o.start_time or self.start_time >= o.end_time):
				raise ValidationError(f'Overlaps with existing schedule {o.start_time}-{o.end_time}')

	def save(self, *args, **kwargs):
		self.full_clean()
		super().save(*args, **kwargs)


class Planner(models.Model):
	"""Per-user planner containing a set of `core.Section` instances."""
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='planner')
	sections = models.ManyToManyField('core.Section', blank=True, related_name='in_planners')

	def __str__(self):
		return f"Planner for {self.user}"

	def total_credits(self):
		# Sum credit value from each section's course
		return sum([s.course.credit or 0 for s in self.sections.select_related('course').all()])


class PlanVariant(models.Model):
	"""Multiple saved planner variants for a single Planner (e.g., Plan 1, Plan 2)."""
	planner = models.ForeignKey(Planner, on_delete=models.CASCADE, related_name='variants')
	name = models.CharField(max_length=120)
	sections = models.ManyToManyField('core.Section', blank=True, related_name='variants')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f"{self.name} ({self.planner.user})"

	def total_credits(self):
		return sum([s.course.credit or 0 for s in self.sections.select_related('course').all()])