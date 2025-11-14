# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Exists, OuterRef
from .models import Prof, Course, Section
from itertools import chain
from django.http import Http404, HttpResponsePermanentRedirect
from review.models import Bookmark

def homepage_view(request):
    return render(request, 'core/homepage.html')

# เพิ่มฟังก์ชันนี้เข้าไป
def about_view(request):
    return render(request, 'core/about.html')

def search(request):
    query = request.GET.get('q', '')
    professors = Prof.objects.none()
    courses = Course.objects.none()
    sections = Section.objects.none()
    all_results = []

    if query:
        # Use __icontains for broad, case-insensitive matching.
        professors = Prof.objects.filter(
            Q(prof_name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

        courses = Course.objects.filter(
            Q(course_code__icontains=query) |
            Q(course_name__icontains=query) |
            Q(description__icontains=query)
        ).distinct()

        sections = Section.objects.filter(
            Q(course__course_code__icontains=query) |
            Q(course__course_name__icontains=query) |
            Q(teachers__prof_name__icontains=query)
        ).select_related('course').prefetch_related('teachers').distinct()

        # Combine all querysets into a single list for the "All" tab
        all_results = sorted(
            list(chain(professors, courses, sections)),
            key=lambda instance: getattr(instance, 'prof_name', getattr(instance, 'course_name', str(instance)))
        )

    context = {
        'query': query,
        'results': all_results, # This is for the "All" tab, which is not currently implemented in the template but the logic is here.
        'professors': professors,
        'courses': courses,
        'sections': sections,
    }
    return render(request, 'core/search.html', context)

def prof_detail(request, pk):
    # Annotate reviews with bookmark status for the current user
    bookmarked_reviews = Bookmark.objects.none()
    if request.user.is_authenticated:
        bookmarked_reviews = Bookmark.objects.filter(
            user=request.user,
            review=OuterRef('pk')
        )

    # Use get_object_or_404 for a direct lookup, which is much more efficient.
    prof = get_object_or_404(
        Prof.objects.prefetch_related('teaching_sections__course'), 
        pk=pk
    )

    reviews = prof.reviews.select_related('user').annotate(is_bookmarked=Exists(bookmarked_reviews))

    return render(request, 'core/prof_detail.html', {'prof': prof, 'reviews': reviews})

def course_detail(request, pk):
    # Annotate reviews with bookmark status for the current user
    bookmarked_reviews = Bookmark.objects.none()
    if request.user.is_authenticated:
        bookmarked_reviews = Bookmark.objects.filter(
            user=request.user,
            review=OuterRef('pk')
        )

    # Simplified to a direct primary key lookup.
    course = get_object_or_404(
        Course.objects.prefetch_related('sections__teachers', 'sections__campus'),
        pk=pk
    )
    
    reviews = course.reviews.select_related('user').annotate(is_bookmarked=Exists(bookmarked_reviews))

    return render(request, 'core/course_detail.html', {'course': course, 'reviews': reviews})