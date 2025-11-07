from django.contrib import admin

# Register your models here.
from .models import Campus, RoomMSTeam, Professor, Course, Section

admin.site.register(Campus)
admin.site.register(RoomMSTeam)
admin.site.register(Professor)
admin.site.register(Course)
admin.site.register(Section)