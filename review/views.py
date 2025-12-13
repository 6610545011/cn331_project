from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
@require_POST
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return JsonResponse({'status': 'ok'})
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, models
from django.views.decorators.http import require_POST
from core.models import Course, Prof, Section
from stats.models import CourseReviewStat
from datetime import date
from django.db.models import F, Q
from .forms import ReviewForm, ReportForm, ReviewUpvoteForm
from .models import Review, Bookmark, Report, ReviewUpvote

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
            # Analytics: increment course review stat
            try:
                today = date.today()
                stat, created = CourseReviewStat.objects.get_or_create(course=review.course, date=today, defaults={'count': 1})
                if not created:
                    CourseReviewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1)
            except Exception:
                pass
            
            messages.success(request, 'ขอบคุณสำหรับรีวิวของคุณ!')
            return redirect('core:homepage')
    else:
        # Ensure the form is instantiated with the current user
        # so dropdowns (courses/professors) are filtered correctly.
        form = ReviewForm(user=request.user)

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


@login_required 
@require_POST
def vote_review(request, review_id):
    # 1. ตรวจสอบและแปลงข้อมูลที่รับเข้ามา
    try:
        data = json.loads(request.body)
        vote_type = int(data.get('vote_type'))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({'status': 'error', 'message': 'Invalid request format.'}, status=400)

    # 2. ตรวจสอบความถูกต้องของ vote_type โดยตรง (แทนการใช้ Form)
    if vote_type not in [1, -1]:
        return JsonResponse({'status': 'error', 'message': 'Invalid vote type.'}, status=400)

    review = get_object_or_404(Review, pk=review_id)
    
    # 3. ใช้ transaction.atomic เพื่อความปลอดภัยของข้อมูล
    with transaction.atomic():
        # หา vote ที่มีอยู่เดิม
        vote, created = ReviewUpvote.objects.get_or_create(
            user=request.user,
            review=review,
            # ใช้ defaults เพื่อกำหนด vote_type เฉพาะตอนที่สร้างใหม่เท่านั้น
            defaults={'vote_type': vote_type}
        )

        if not created:
            # ถ้า vote มีอยู่แล้ว (ไม่ได้สร้างใหม่)
            if vote.vote_type == vote_type:
                # ถ้ากดซ้ำ -> ลบทิ้ง
                vote.delete()
                user_vote_status = 0  # 0 หมายถึงไม่มี vote
            else:
                # ถ้ากดตรงข้าม -> อัปเดต
                vote.vote_type = vote_type
                vote.save()
                user_vote_status = vote_type
        else:
            # ถ้าเพิ่งสร้าง vote ใหม่
            user_vote_status = vote_type

    # 4. คำนวณคะแนนใหม่โดยใช้ property จาก model ที่เราสร้างไว้
    # การทำแบบนี้ทำให้ View ไม่ต้องรู้ว่าคะแนนคำนวณอย่างไร
    new_score = review.vote_score
    
    return JsonResponse({
        'status': 'ok',
        'new_score': new_score,
        'user_vote': user_vote_status
    })