from django.contrib import admin

# Register your models here.
from .models import Course, Prof, Campus, Section, Teach, SectionTime, Enrollment

admin.site.register(Campus)
admin.site.register(Prof)
admin.site.register(Course)
admin.site.register(Section)
admin.site.register(Teach)
admin.site.register(Enrollment)
# Stats are registered under the separate 'stats' app admin