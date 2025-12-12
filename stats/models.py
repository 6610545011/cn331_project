from django.db import models
from django.conf import settings


class DailyActiveUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_active_records')
    date = models.DateField()

    class Meta:
        managed = False
        db_table = 'core_dailyactiveuser'
        unique_together = ('user', 'date')
        indexes = [models.Index(fields=['date'])]

    def __str__(self):
        return f"Active {self.user} on {self.date}"


class CourseSearchStat(models.Model):
    course = models.ForeignKey('core.Course', on_delete=models.CASCADE, related_name='search_stats')
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'core_coursesearchstat'
        unique_together = ('course', 'date')
        indexes = [models.Index(fields=['date']), models.Index(fields=['course'])]

    def __str__(self):
        return f"{self.course.course_code} searches on {self.date}: {self.count}"


class CourseViewStat(models.Model):
    course = models.ForeignKey('core.Course', on_delete=models.CASCADE, related_name='view_stats')
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'core_courseviewstat'
        unique_together = ('course', 'date')
        indexes = [models.Index(fields=['date']), models.Index(fields=['course'])]

    def __str__(self):
        return f"{self.course.course_code} views on {self.date}: {self.count}"


class CourseReviewStat(models.Model):
    course = models.ForeignKey('core.Course', on_delete=models.CASCADE, related_name='review_stats')
    date = models.DateField()
    count = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'core_coursereviewstat'
        unique_together = ('course', 'date')
        indexes = [models.Index(fields=['date']), models.Index(fields=['course'])]

    def __str__(self):
        return f"{self.course.course_code} reviews on {self.date}: {self.count}"
