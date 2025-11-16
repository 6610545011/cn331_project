# core/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Exists, OuterRef, Sum
from django.db.models.functions import Coalesce
from .models import Prof, Course, Section
from itertools import chain
from review.models import Bookmark, Review

# ==================================
#  Simple Views
# ==================================

def homepage_view(request):
    return render(request, 'core/homepage.html')

def about_view(request):
    return render(request, 'core/about.html')

# ==================================
#  Search View
# ==================================

def search(request):
    query = request.GET.get('q', '')
    sort_by = request.GET.get('sort_by', 'alphabetical')
    order = request.GET.get('order', 'asc')
    order_prefix = '-' if order == 'desc' else ''

    # --- สร้าง subquery สำหรับเช็ค bookmark ก่อน ---
    user_bookmark_subquery = Bookmark.objects.none()
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(
            user=request.user, review=OuterRef('pk')
        )

    # --- สร้าง QuerySet พื้นฐานสำหรับ Review พร้อม Annotation ---
    reviews_queryset = Review.objects.annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user=request.user)), 0)
    ).select_related('course', 'prof', 'user').distinct()

    if query:
        # --- กรองข้อมูลตาม query ---
        professors = Prof.objects.filter(
            Q(prof_name__icontains=query) | Q(description__icontains=query)
        ).distinct()

        courses = Course.objects.filter(
            Q(course_code__icontains=query) | Q(course_name__icontains=query) | Q(description__icontains=query)
        ).distinct()

        sections = Section.objects.filter(
            Q(course__course_code__icontains=query) | Q(course__course_name__icontains=query) | Q(teachers__prof_name__icontains=query)
        ).select_related('course').prefetch_related('teachers').distinct()

        reviews = reviews_queryset.filter(
            Q(head__icontains=query) | Q(body__icontains=query)
        )
    else:
        # --- ถ้าไม่มี query ให้ดึงข้อมูลทั้งหมด ---
        professors = Prof.objects.all()
        courses = Course.objects.all()
        sections = Section.objects.select_related('course').prefetch_related('teachers').all()
        reviews = reviews_queryset.all()
    
    # --- จัดเรียงข้อมูล ---
    if sort_by == 'alphabetical':
        professors = professors.order_by(f'{order_prefix}prof_name')
        courses = courses.order_by(f'{order_prefix}course_name')
        sections = sections.order_by(f'{order_prefix}course__course_name', f'{order_prefix}section_number')
        reviews = reviews.order_by(f'{order_prefix}head')

    # --- รวมผลลัพธ์ทั้งหมดสำหรับแท็บ "All" ---
    all_results = sorted(
        list(chain(professors, courses, sections, reviews)),
        key=lambda instance: getattr(instance, 'prof_name', 
                                 getattr(instance, 'course_name', 
                                         getattr(instance, 'head', str(instance)))),
        reverse=(order == 'desc')
    )

    context = {
        'query': query,
        'sort_by': sort_by,
        'order': order,
        'results': all_results,
        'professors': professors,
        'courses': courses,
        'sections': sections,
        'reviews': reviews,
    }
    return render(request, 'core/search.html', context)

# ==================================
#  Detail Views
# ==================================

def prof_detail(request, pk):
    prof = get_object_or_404(Prof.objects.prefetch_related('teaching_sections__course'), pk=pk)

    # สร้าง subquery สำหรับเช็ค bookmark (เฉพาะ user ที่ login)
    user_bookmark_subquery = Bookmark.objects.filter(user=request.user, review=OuterRef('pk')) if request.user.is_authenticated else Bookmark.objects.none()

    # Annotate รีวิวสำหรับอาจารย์คนนี้
    reviews = prof.reviews.select_related('user', 'course').annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        # แก้ไข: เปลี่ยนชื่อ annotation จาก 'vote_score' เป็น 'score'
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user=request.user)), 0)
    ).distinct()

    return render(request, 'core/prof_detail.html', {'prof': prof, 'reviews': reviews})


def course_detail(request, pk):
    course = get_object_or_404(Course.objects.prefetch_related('sections__teachers', 'sections__campus'), pk=pk)
    
    # สร้าง subquery สำหรับเช็ค bookmark (เฉพาะ user ที่ login)
    user_bookmark_subquery = Bookmark.objects.filter(user=request.user, review=OuterRef('pk')) if request.user.is_authenticated else Bookmark.objects.none()
    
    # Annotate รีวิวสำหรับคอร์สนี้
    reviews = course.reviews.select_related('user', 'prof').annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        # แก้ไข: เปลี่ยนชื่อ annotation จาก 'vote_score' เป็น 'score'
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user=request.user)), 0)
    ).distinct()

    return render(request, 'core/course_detail.html', {'course': course, 'reviews': reviews})