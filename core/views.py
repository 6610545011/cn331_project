# core/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.text import slugify
from .models import Professor, Course, Section
from itertools import chain
from django.http import Http404

def homepage_view(request):
    return render(request, 'core/homepage.html')

# เพิ่มฟังก์ชันนี้เข้าไป
def about_view(request):
    return render(request, 'core/about.html')

def search(request):
    query = request.GET.get('q', '')
    professors = Professor.objects.none()
    courses = Course.objects.none()
    sections = Section.objects.none()
    all_results = []

    if query:
        # Use __iregex for better Unicode character support (including Thai)
        professors = Professor.objects.filter(
            Q(name__iregex=query) |
            Q(description__iregex=query)
        ).distinct()
        courses = Course.objects.filter(
            Q(code__iregex=query) |
            Q(name__iregex=query) |
            Q(description__iregex=query)
        ).distinct()
        sections = Section.objects.filter(
            Q(course__name__iregex=query) |
            Q(professor__name__iregex=query)
        ).distinct()

        # Combine all querysets into a single list for the "All" tab
        all_results = sorted(
            list(chain(professors, courses, sections)),
            key=lambda instance: instance.name
        )

    context = {
        'query': query,
        'results': all_results,
        'professors': professors,
        'courses': courses,
        'sections': sections,
    }
    return render(request, 'core/search.html', context)



def prof_detail(request, slug):
    # This is inefficient. Let's find the professor whose slugified name matches.
    # Note: This can still be slow on large datasets. A dedicated slug field is better.
    professors = Professor.objects.all().prefetch_related('section_set__course', 'review_set__user')
    for prof in professors:
        if slugify(prof.name, allow_unicode=True) == slug:
            return render(request, 'core/prof_detail.html', {'prof': prof})
    raise Http404("Professor not found or slug could not be matched.")

def course_detail(request, slug):
    # This is also inefficient. We'll find the specific course.
    # Using prefetch_related to optimize fetching related sections and their professors.
    courses = Course.objects.all().prefetch_related('section_set__professor', 'section_set__campus', 'section_set__room')
    for course in courses:
        # Using allow_unicode=True to better handle names with non-latin characters
        if slugify(course.name, allow_unicode=True) == slug:
            return render(request, 'core/course_detail.html', {'course': course})
    raise Http404("Course not found or slug could not be matched.")