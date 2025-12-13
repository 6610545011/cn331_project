from django.contrib import admin
from core.models import Section
from .models import SectionSchedule, Planner, PlanVariant


class SectionScheduleInline(admin.TabularInline):
	model = SectionSchedule
	extra = 1
	fields = ('day_of_week', 'start_time', 'end_time')


class SectionAdminWithSchedule(admin.ModelAdmin):
	inlines = [SectionScheduleInline]
	list_display = ('__str__', 'course', 'section_number')
	search_fields = ('section_number', 'course__course_code', 'course__course_name')


# Replace existing Section admin registration with one that includes schedules
try:
	admin.site.unregister(Section)
except Exception:
	pass

admin.site.register(Section, SectionAdminWithSchedule)


@admin.register(SectionSchedule)
class SectionScheduleAdmin(admin.ModelAdmin):
	list_display = ('section', 'day_of_week', 'start_time', 'end_time')
	list_filter = ('day_of_week',)


@admin.register(Planner)
class PlannerAdmin(admin.ModelAdmin):
	list_display = ('user',)


@admin.register(PlanVariant)
class PlanVariantAdmin(admin.ModelAdmin):
	list_display = ('name', 'planner', 'created_at')
	filter_horizontal = ('sections',)
