from django.contrib import admin

# Register your models here.
from .models import Campus, Prof, Course, Section

admin.site.register(Campus)
admin.site.register(Prof)
admin.site.register(Course)
admin.site.register(Section)