from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError

from .models import Planner, SectionSchedule, PlanVariant
from core.models import Section
from . import utils

import hashlib


@login_required
def add_section_to_planner(request, section_id):
	"""Add a section to the logged-in user's planner after conflict checks.

	Returns JSON with success/warning details.
	"""
	user = request.user
	planner, _ = Planner.objects.get_or_create(user=user)
	section = get_object_or_404(Section, pk=section_id)

	# Check time conflicts
	try:
		result = utils.check_conflicts(planner, section)
	except ValidationError as e:
		return JsonResponse({'ok': False, 'error': str(e.message_dict if hasattr(e, 'message_dict') else e.messages)}, status=400)

	# No conflict; add to planner
	planner.sections.add(section)

	response = {'ok': True, 'message': 'Section added'}
	if result.get('warning'):
		response['warning'] = result['warning']
	response['total_credits'] = result.get('total_credits')
	return JsonResponse(response)


@login_required
def remove_section_from_planner(request, section_id):
	user = request.user
	planner = getattr(user, 'planner', None)
	section = get_object_or_404(Section, pk=section_id)
	if not planner:
		return JsonResponse({'ok': False, 'error': 'Planner not found'}, status=404)

	planner.sections.remove(section)
	total = planner.total_credits() if hasattr(planner, 'total_credits') else sum([s.course.credit or 0 for s in planner.sections.select_related('course').all()])
	return JsonResponse({'ok': True, 'message': 'Section removed', 'total_credits': total})


def _pastel_color_for_key(key: str) -> str:
	"""Generate a pastel HSL color from a key string."""
	h = int(hashlib.md5(key.encode('utf-8')).hexdigest()[:8], 16) % 360
	# pastel saturation and lightness
	s = 65
	l = 85
	return f"hsl({h}deg {s}% {l}%)"


@login_required
def planner_view(request):
	"""Render a timetable-style planner.

	Precomputes css positions for CSS Grid and a color per course.
	"""
	user = request.user
	planner, _ = Planner.objects.get_or_create(user=user)

	# Build timetable items: for each SectionSchedule row, compute grid placement
	items = []

	# helper to compute slot index relative to 08:00
	def time_to_slot_index(t):
		return int(((t.hour * 60 + t.minute) - (utils.SLOT_START.hour * 60 + utils.SLOT_START.minute)) / utils.SLOT_DURATION_MINUTES)

	for section in planner.sections.select_related('course').all():
		# get professor name (first teacher if exists)
		prof = section.teachers.first()
		prof_name = prof.prof_name if prof else ''

		# For each schedule row
		for ss in SectionSchedule.objects.filter(section=section):
			# compute start slot and span
			start_slot = time_to_slot_index(ss.start_time)
			# compute duration in minutes
			duration_minutes = (ss.end_time.hour * 60 + ss.end_time.minute) - (ss.start_time.hour * 60 + ss.start_time.minute)
			span = max(1, int((duration_minutes + utils.SLOT_DURATION_MINUTES - 1) // utils.SLOT_DURATION_MINUTES))

			css_start_col = 2 + start_slot  # column 1 is day label
			css_span_col = span

			key = f"{section.course.course_code}-{section.section_number}-{ss.day_of_week}"
			color = _pastel_color_for_key(key)

			items.append({
				'course_code': section.course.course_code,
				'course_name': section.course.course_name,
				'section_number': section.section_number,
				'room': section.room,
				'professor': prof_name,
				'day': ss.day_of_week,  # 0=Mon .. 6=Sun
				'css_start_col': css_start_col,
				'css_span_col': css_span_col,
				'color': color,
			})

	# Build course list for bottom table (unique sections)
	course_rows = []
	for section in planner.sections.select_related('course').all():
		prof = section.teachers.first()
		prof_name = prof.prof_name if prof else ''
		course_rows.append({
			'course_code': section.course.course_code,
			'course_name': section.course.course_name,
			'section_number': section.section_number,
			'professor': prof_name,
			'section_id': section.id,
		})

	# also provide user's sections for the add-schedule form (planner sections)
	user_sections = [{'id': s.id, 'label': f"{s.course.course_code} Sec {s.section_number}"} for s in planner.sections.select_related('course').all()]
	user_section_ids = [s.id for s in planner.sections.all()]  # For JS to mark already-added sections

	# for future planner: provide ALL sections to browse/add
	all_sections = [{'id': s.id, 'code': s.course.course_code, 'name': s.course.course_name, 'sec': s.section_number} for s in Section.objects.select_related('course').all().order_by('course__course_code', 'section_number')]

	context = {
		'planner': planner,
		'items': items,
		'days': ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
		'slot_count': utils.SLOTS_PER_DAY,
		'slot_start_hour': utils.SLOT_START.hour,
		'slot_indices': list(range(utils.SLOTS_PER_DAY)),
		'slot_labels': [f"{(utils.SLOT_START.hour + ((i*utils.SLOT_DURATION_MINUTES)//60))%24:02d}:{(i*utils.SLOT_DURATION_MINUTES)%60:02d}" for i in range(utils.SLOTS_PER_DAY)],
		'days_enum': [{'idx': i, 'name': name} for i, name in enumerate(['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])],
		'course_rows': course_rows,
		'user_sections': user_sections,
		'user_section_ids': user_section_ids,  # JS array for marking added sections
		'all_sections': all_sections,
	}
	return render(request, 'planner/index.html', context)



@login_required
def add_section_schedule(request):
	"""Allow authenticated users to add a SectionSchedule (half-hour aligned) for a section.

	Expects POST with: section_id, day (0-6), start_slot (0-23), span (number of 30-min slots)
	"""
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

	section_id = request.POST.get('section_id') or request.POST.get('section')
	day = request.POST.get('day')
	start_slot = request.POST.get('start_slot')
	span = request.POST.get('span')

	if not all([section_id, day, start_slot, span]):
		return JsonResponse({'ok': False, 'error': 'Missing parameters'}, status=400)

	try:
		section = Section.objects.get(pk=int(section_id))
	except Section.DoesNotExist:
		return JsonResponse({'ok': False, 'error': 'Section not found'}, status=404)

	try:
		day_i = int(day)
		start_i = int(start_slot)
		span_i = int(span)
	except ValueError:
		return JsonResponse({'ok': False, 'error': 'Invalid numeric parameters'}, status=400)

	# compute times
	from datetime import datetime, timedelta, time
	slot_minutes = utils.SLOT_DURATION_MINUTES
	base = utils.SLOT_START
	start_minutes = base.hour * 60 + base.minute + start_i * slot_minutes
	end_minutes = start_minutes + span_i * slot_minutes

	start_time = time(start_minutes // 60, start_minutes % 60)
	end_time = time(end_minutes // 60, end_minutes % 60)

	# Validate within allowed range
	if start_i < 0 or start_i >= utils.SLOTS_PER_DAY or (start_i + span_i) > utils.SLOTS_PER_DAY:
		return JsonResponse({'ok': False, 'error': 'Slot range out of bounds'}, status=400)

	# Create SectionSchedule (model's clean/save will enforce more validation)
	try:
		ss = SectionSchedule.objects.create(section=section, day_of_week=day_i, start_time=start_time, end_time=end_time)
	except Exception as e:
		return JsonResponse({'ok': False, 'error': str(e)}, status=400)

	return JsonResponse({'ok': True, 'message': 'Schedule added', 'id': ss.id})


@login_required
def create_variant(request):
	"""Create a new PlanVariant for the current user (POST: name).

	Returns JSON: {ok: True, id, name}
	"""
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

	name = request.POST.get('name') or request.POST.get('variant_name')
	if not name:
		return JsonResponse({'ok': False, 'error': 'Name required'}, status=400)

	planner, _ = Planner.objects.get_or_create(user=request.user)
	variant = PlanVariant.objects.create(planner=planner, name=name)
	return JsonResponse({'ok': True, 'id': variant.id, 'name': variant.name})


@login_required
def list_variants(request):
	"""Return JSON list of user's PlanVariants."""
	planner, _ = Planner.objects.get_or_create(user=request.user)
	variants = [{'id': v.id, 'name': v.name, 'credits': v.total_credits()} for v in planner.variants.all()]
	return JsonResponse({'ok': True, 'variants': variants})


@login_required
def add_section_to_variant(request, variant_id, section_id):
	"""Add a section to a specific PlanVariant after conflict checks."""
	variant = get_object_or_404(PlanVariant, pk=variant_id, planner__user=request.user)
	section = get_object_or_404(Section, pk=section_id)

	try:
		result = utils.check_conflicts(variant, section)
	except ValidationError as e:
		return JsonResponse({'ok': False, 'error': str(e.message_dict if hasattr(e, 'message_dict') else e.messages)}, status=400)

	variant.sections.add(section)
	resp = {'ok': True, 'message': 'Section added', 'variant_id': variant.id, 'total_credits': result.get('total_credits')}
	if result.get('warning'):
		resp['warning'] = result.get('warning')
	return JsonResponse(resp)


@login_required
def remove_section_from_variant(request, variant_id, section_id):
	variant = get_object_or_404(PlanVariant, pk=variant_id, planner__user=request.user)
	section = get_object_or_404(Section, pk=section_id)
	variant.sections.remove(section)
	return JsonResponse({'ok': True, 'message': 'Section removed', 'variant_id': variant.id, 'total_credits': variant.total_credits()})


@login_required
def save_current_variant(request):
	"""Create a PlanVariant from the current planner and copy all sections into it.

	Expects POST {'name': <variant name>}
	"""
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

	name = request.POST.get('name') or request.POST.get('variant_name')
	if not name:
		return JsonResponse({'ok': False, 'error': 'Name required'}, status=400)

	planner, _ = Planner.objects.get_or_create(user=request.user)
	sections = planner.sections.select_related('course').all()
	total = sum([s.course.credit or 0 for s in sections])
	# enforce credit limits
	if total < 9 or total > 22:
		return JsonResponse({'ok': False, 'error': f'Total credits must be between 9 and 22. Current: {total}'} , status=400)

	variant = PlanVariant.objects.create(planner=planner, name=name)
	if sections.exists():
		variant.sections.set(sections)
	return JsonResponse({'ok': True, 'id': variant.id, 'name': variant.name, 'total_credits': variant.total_credits()})


@login_required
def load_variant(request, variant_id):
	"""Load a saved variant into the user's active planner (replace current planner sections).

	POST only.
	"""
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

	variant = get_object_or_404(PlanVariant, pk=variant_id, planner__user=request.user)
	planner, _ = Planner.objects.get_or_create(user=request.user)
	planner.sections.set(variant.sections.all())
	return JsonResponse({'ok': True, 'message': 'Variant loaded', 'variant_id': variant.id, 'total_credits': planner.total_credits()})


@login_required
def delete_variant(request, variant_id):
	"""Delete a saved PlanVariant."""
	if request.method != 'POST':
		return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

	variant = get_object_or_404(PlanVariant, pk=variant_id, planner__user=request.user)
	variant.delete()
	return JsonResponse({'ok': True, 'message': 'Variant deleted', 'variant_id': variant_id})


@login_required
def search_sections(request):
	"""Search all available sections by course code or name."""
	q = request.GET.get('q', '').lower()
	sections = Section.objects.select_related('course').all()
	
	if q:
		from django.db.models import Q
		sections = sections.filter(
			Q(course__course_code__icontains=q) | 
			Q(course__course_name__icontains=q)
		)
	
	results = [
		{
			'id': s.id,
			'code': s.course.course_code,
			'name': s.course.course_name,
			'sec': s.section_number,
			'credit': s.course.credit or 0,
			'label': f"{s.course.course_code} Sec {s.section_number} - {s.course.course_name}",
		}
		for s in sections[:20]  # limit to 20 results
	]
	return JsonResponse({'ok': True, 'results': results})

