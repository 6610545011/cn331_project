from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReviewForm
from .models import Review

from django.http import JsonResponse
from django.db.models import Q
from core.models import Course, Professor, Section

# Create your views here.

@login_required # บังคับให้ต้อง login ก่อนถึงจะเขียนรีวิวได้
def write_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            # สร้าง object review แต่ยังไม่ save ลง db
            review = form.save(commit=False)
            # กำหนด user ให้เป็น user ที่ login อยู่
            review.user = request.user
            # บันทึกลง db
            review.save()
            
            messages.success(request, 'ขอบคุณสำหรับรีวิวของคุณ!')
            return redirect('core:homepage') # กลับไปที่หน้าแรกหลังรีวิวสำเร็จ
    else:
        form = ReviewForm()

    context = {
        'form': form
    }
    return render(request, 'review/write_review.html', context)

def search_courses(request):
    """
    API endpoint สำหรับค้นหารายวิชาเพื่อใช้กับ Select2
    """
    term = request.GET.get('term', '')
    
    # --- แก้ไขตรงนี้ ---
    # เปลี่ยนจาก 'course_code__icontains' เป็น 'code__icontains'
    courses = Course.objects.filter(
        Q(code__icontains=term) | Q(name__icontains=term)
    )[:20]

    results = []
    for course in courses:
        # --- และแก้ไขตรงนี้ ---
        # เปลี่ยนจาก 'course.course_code' เป็น 'course.code'
        results.append({
            'id': course.id,
            'text': f"{course.code} - {course.name}"
        })
    
    return JsonResponse({'results': results})


def get_professors_for_course(request):
    """
    API endpoint สำหรับดึงรายชื่ออาจารย์ที่สอนในรายวิชาที่เลือก
    """
    course_id = request.GET.get('course_id')
    if not course_id:
        return JsonResponse({'professors': []})

    # ค้นหาอาจารย์จาก Section ที่เกี่ยวข้องกับ Course ID นี้
    # .distinct() เพื่อไม่ให้มีชื่ออาจารย์ซ้ำ
    professors = Professor.objects.filter(
        section__course_id=course_id
    ).distinct().order_by('name')

    results = [{'id': p.id, 'name': p.name} for p in professors]
    
    return JsonResponse({'professors': results})