from django.contrib import admin
from .models import DailyActiveUser, CourseSearchStat, CourseViewStat, CourseReviewStat

@admin.register(DailyActiveUser)
class DailyActiveUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    list_filter = ('date', 'user')

@admin.register(CourseSearchStat)
class CourseSearchStatAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'count')
    list_filter = ('date', 'course')
    search_fields = ('course__course_code',)

@admin.register(CourseViewStat)
class CourseViewStatAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'count')
    list_filter = ('date', 'course')
    search_fields = ('course__course_code',)

@admin.register(CourseReviewStat)
class CourseReviewStatAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'count')
    list_filter = ('date', 'course')
    search_fields = ('course__course_code',)
