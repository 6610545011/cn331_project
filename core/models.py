from django.db import models
from django.conf import settings # Used for referencing the custom User model

# Core Entities
class Course(models.Model):
    id = models.AutoField(primary_key=True)
    course_name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    credit = models.IntegerField()

    @property
    def all_professors(self):
        """
        Returns a queryset of all unique professors teaching any section of this course.
        """
        return Prof.objects.filter(teaching_sections__course=self).distinct()

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

class Prof(models.Model):
    id = models.AutoField(primary_key=True)
    prof_name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    imgurl = models.URLField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.prof_name

class Campus(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
    # slot_id is renamed to id for Django standard practice
    id = models.AutoField(primary_key=True) 
    time = models.CharField(max_length=100) # e.g., "MWF 10:00 - 10:50"

    def __str__(self):
        return self.time

class Section(models.Model):
    id = models.AutoField(primary_key=True)
    section_number = models.CharField(max_length=50)
    
    # Relationships
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    
    # Schedule details (stored as char based on DBML, but ideally broken down in real life)
    datetime = models.CharField(max_length=255, blank=True)
    room = models.CharField(max_length=100, blank=True)
    campus = models.ForeignKey(Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')

    # M2M Relationships defined via explicit "through" models below
    teachers = models.ManyToManyField(Prof, through='Teach', related_name='teaching_sections')
    schedule = models.ManyToManyField(TimeSlot, through='SectionTime', related_name='scheduled_sections')
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment', related_name='enrolled_sections')

    def __str__(self):
        return f"{self.course.course_code} Section {self.section_number}"


# Middle Tables (Many-to-Many defined explicitly in DBML)

class Enrollment(models.Model):
    """Links User to Section (Enrollment)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('user', 'section'),)
        verbose_name_plural = "Enrollments"

    def __str__(self):
        return f"{self.user.email} enrolled in {self.section}"


class SectionTime(models.Model):
    """Links Section to TimeSlot"""
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    # Refers to TimeSlot.id (which was slot_id)
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE) 

    class Meta:
        unique_together = (('section', 'slot'),)

    def __str__(self):
        return f"Section {self.section.id} at {self.slot.time}"


class Teach(models.Model):
    """Links Prof to Section"""
    prof = models.ForeignKey(Prof, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('prof', 'section'),)
        verbose_name_plural = "Teaching Assignments"

    def __str__(self):
        return f"{self.prof.prof_name} teaches {self.section}"