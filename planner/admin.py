from django.contrib import admin

# Register your models here.
from .models import Schedule, ScheduleSection, Enrollment

admin.site.register(Schedule)
admin.site.register(ScheduleSection)
admin.site.register(Enrollment)