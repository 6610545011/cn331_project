from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from core.models import Course, Prof, Section
from .forms import ReviewForm, ReportForm
from .models import Review, Bookmark, Report


@login_required
def write_review(request):
    # ... (ส่วนนี้ไม่ต้องแก้ไข) ...
    if request.method == 'POST':
        form = ReviewForm(request.POST)
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
    """
    Toggles a bookmark on a review for the current user.
    Creates a bookmark if it doesn't exist, deletes it if it does.
    """
    review = get_object_or_404(Review, id=review_id)
    
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        course=review.course,
        review=review
    )

    if not created:
        bookmark.delete()
        return JsonResponse({'status': 'ok', 'bookmarked': False})
    
    return JsonResponse({'status': 'ok', 'bookmarked': True})


@login_required
@require_POST
def report_review(request, review_id):
    """
    Handles the submission of a report for a review.
    """
    review = get_object_or_404(Review, id=review_id)
    form = ReportForm(request.POST)

    if form.is_valid():
        # Check if the user has already reported this review
        if Report.objects.filter(user=request.user, review=review).exists():
            return JsonResponse({'status': 'error', 'message': 'You have already reported this review.'}, status=409)

        report = form.save(commit=False)
        report.user = request.user
        report.review = review
        report.save()
        return JsonResponse({'status': 'ok', 'message': 'Thank you for your report. We will review it shortly.'})
    
    # Extract form errors to send back as JSON
    errors = form.errors.as_json()
    return JsonResponse({'status': 'error', 'errors': errors}, status=400)