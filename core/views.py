# core/views.py
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage
from django.template.loader import render_to_string
from django.db.models import Q, Exists, OuterRef, Sum, F
from django.utils import timezone
from datetime import date
from core.models import Prof, Course, Section
from stats.models import CourseSearchStat, CourseViewStat
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from itertools import chain
from review.models import Bookmark, Review

# ==================================
#  Simple Views
# ==================================

def homepage_view(request):
    # Show the first page of latest reviews on the homepage
    user_bookmark_subquery = Bookmark.objects.none()
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(user=request.user, review=OuterRef('pk'))

    reviews_qs = Review.objects.annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user_id=request.user.id)), 0)
    ).select_related('user', 'course', 'prof').order_by('-date_created')
    paginator = Paginator(reviews_qs, 10)
    page_obj = paginator.page(1)

    context = {
        'reviews': page_obj.object_list,
        'has_next': page_obj.has_next(),
        'next_page': 2 if page_obj.has_next() else None,
    }
    return render(request, 'core/homepage.html', context)


def latest_reviews_api(request):
    """
    Paginated AJAX endpoint returning rendered review blocks.
    Query params: page (1-based), page_size
    """
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    user_bookmark_subquery = Bookmark.objects.none()
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(user=request.user, review=OuterRef('pk'))

    reviews_qs = Review.objects.annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user_id=request.user.id)), 0)
    ).select_related('user', 'course', 'prof').order_by('-date_created')

    paginator = Paginator(reviews_qs, page_size)
    try:
        page_obj = paginator.page(page)
    except EmptyPage:
        return JsonResponse({'reviews_html': '', 'has_next': False, 'next_page': None})

    rendered_blocks = []
    for rev in page_obj.object_list:
        html = render_to_string('review/includes/review_block.html', {'review': rev, 'user': request.user}, request=request)
        rendered_blocks.append(html)

    return JsonResponse({
        'reviews_html': ''.join(rendered_blocks),
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None
    })

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
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user_id=request.user.id)), 0)
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
    # --- Analytics: increment course search stats when courses are present in results
    if query and courses.exists():
        today = date.today()
        # Only increment top N matched course stats to reduce write amplification (e.g., top 5)
        for course in courses[:5]:
            stat, created = CourseSearchStat.objects.get_or_create(course=course, date=today, defaults={'count': 1})
            if not created:
                CourseSearchStat.objects.filter(pk=stat.pk).update(count=F('count') + 1)
    
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
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user_id=request.user.id)), 0)
    ).distinct()

    return render(request, 'core/prof_detail.html', {'prof': prof, 'reviews': reviews})


def course_detail(request, course_code):
    course = get_object_or_404(Course, course_code__iexact=course_code)
    
    # Check if the course is bookmarked by the current user (review=None)
    course_is_bookmarked = False
    if request.user.is_authenticated:
        course_is_bookmarked = Bookmark.objects.filter(
            user=request.user,
            course=course,
            review=None
        ).exists()
    
    # สร้าง subquery สำหรับเช็ค bookmark (เฉพาะ user ที่ login)
    # A review is bookmarked if either:
    # 1. The specific review is bookmarked (review=OuterRef('pk'))
    # 2. The course is bookmarked (review=None)
    if request.user.is_authenticated:
        user_bookmark_subquery = Bookmark.objects.filter(
            user=request.user,
            course=course
        ).filter(
            Q(review=OuterRef('pk')) | Q(review=None)
        )
    else:
        user_bookmark_subquery = Bookmark.objects.none()
    
    # Annotate รีวิวสำหรับคอร์สนี้
    reviews = course.reviews.select_related('user', 'prof').annotate(
        is_bookmarked=Exists(user_bookmark_subquery),
        # แก้ไข: เปลี่ยนชื่อ annotation จาก 'vote_score' เป็น 'score'
        score=Coalesce(Sum('votes__vote_type'), 0),
        user_vote=Coalesce(Sum('votes__vote_type', filter=Q(votes__user_id=request.user.id)), 0)
    ).distinct()

    # --- Analytics: increment view count ---
    today = date.today()
    stat, created = CourseViewStat.objects.get_or_create(course=course, date=today, defaults={'count': 1})
    if not created:
        CourseViewStat.objects.filter(pk=stat.pk).update(count=F('count') + 1)

    return render(request, 'core/course_detail.html', {
        'course': course,
        'reviews': reviews,
        'course_is_bookmarked': course_is_bookmarked
    })




@login_required
@require_POST
def toggle_course_bookmark(request, course_id):
    """
    Toggles a bookmark on a course for the current user.
    Creates a bookmark if it doesn't exist, deletes it if it does.
    """
    course = get_object_or_404(Course, id=course_id)
    
    bookmark, created = Bookmark.objects.get_or_create(
        user=request.user,
        course=course,
        review=None
    )

    if not created:
        bookmark.delete()
        return JsonResponse({'status': 'ok', 'bookmarked': False})

    return JsonResponse({'status': 'ok', 'bookmarked': True})