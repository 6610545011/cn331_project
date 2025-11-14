# review/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest, Http404
from django.views.decorators.http import require_POST
from django.db import transaction
from django.db.models import Q, Sum

from .forms import ReviewForm, ReportForm, ReviewUpvoteForm
from .models import Review, Bookmark, Report, ReviewUpvote
from core.models import Course, Section, Prof


@login_required
def write_review(request):
    # ... (ส่วนนี้ไม่ต้องแก้ไข) ...
    if request.method == 'POST':
        # ส่ง request.user เข้าไปในฟอร์มตอนประมวลผลข้อมูล
        form = ReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            form.save_m2m() # จำเป็นถ้าฟอร์มมี ManyToManyFields
            
            messages.success(request, 'ขอบคุณสำหรับรีวิวของคุณ!')
            return redirect('core:homepage')
    else:
        form = ReviewForm()

    context = {
        'form': form
    }
    return render(request, 'review/write_review.html', context)


def ajax_search_courses(request):
    # ... (ส่วนนี้ไม่ต้องแก้ไข) ...
    term = request.GET.get('term', '')
    courses = Course.objects.filter(
        Q(course_code__icontains=term) | Q(course_name__icontains=term)
    )[:20]
    results = [{'id': course.id, 'text': f"{course.course_code} - {course.course_name}"} for course in courses]
    return JsonResponse({'results': results})


# --- แก้ไขฟังก์ชันนี้ ---
def ajax_get_professors(request):
    """
    API endpoint สำหรับดึงรายชื่ออาจารย์ที่สอนใน Section ที่เลือก
    """
    # 1. เปลี่ยนมารับ section_id แทน course_id
    section_id = request.GET.get('section_id')
    if not section_id:
        return JsonResponse({'professors': []})

    # 2. ค้นหาอาจารย์จากตาราง Teach ที่เชื่อมกับ Section ID นี้โดยตรง
    professors = Prof.objects.filter(
        teach__section_id=section_id
    ).distinct().order_by('prof_name')

    results = [{'id': p.id, 'name': p.prof_name} for p in professors]
    
    return JsonResponse({'professors': results})


def ajax_get_sections(request):
    # ... (ส่วนนี้ไม่ต้องแก้ไข) ...
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'sections': []})
    sections = Section.objects.filter(course_id=course_id).order_by('section_number')
    results = [{'id': s.id, 'text': f"Section {s.section_number}"} for s in sections]
    return JsonResponse({'sections': results})


@login_required
@require_POST
def toggle_bookmark(request, review_id):
    # Placeholder for your bookmark logic
    review = get_object_or_404(Review, pk=review_id)
    # ... your logic here ...
    return JsonResponse({'status': 'ok', 'bookmarked': True})


@login_required
@require_POST
def report_review(request, review_id):
    # Placeholder for your report logic
    review = get_object_or_404(Review, pk=review_id)
    # ... your logic here ...
    return JsonResponse({'status': 'ok', 'message': 'Report submitted.'})


# Placeholder for your AJAX views
def ajax_search_courses(request):
    return JsonResponse({'results': []})

def ajax_get_professors(request):
    return JsonResponse({'professors': []})

def ajax_get_sections_for_course(request):
    return JsonResponse({'sections': []})