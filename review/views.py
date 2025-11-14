from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from core.models import Course, Prof, Section
from .forms import ReviewForm
from .models import Review


@login_required
def write_review(request):
    if request.method == 'POST':
        # ส่ง request.user เข้าไปในฟอร์มตอนประมวลผลข้อมูล
        form = ReviewForm(request.POST, user=request.user)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.save()
            form.save_m2m()
            messages.success(request, 'ขอบคุณสำหรับรีวิวของคุณ!')
            return redirect('core:homepage')
    else:
        # ส่ง request.user เข้าไปในฟอร์มตอนแสดงหน้าเว็บครั้งแรก
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
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'sections': []})
    
    # (เพิ่ม) กรองเฉพาะ Section ที่ user คนนี้เคยลงทะเบียน
    sections = Section.objects.filter(
        course_id=course_id, 
        students=request.user
    ).distinct().order_by('section_number')
    
    results = [{'id': s.id, 'text': f"Section {s.section_number}"} for s in sections]
    return JsonResponse({'sections': results})