# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, F
from django.utils.text import slugify
from .models import Professor, Course, Section
from itertools import chain
from django.http import Http404, HttpResponsePermanentRedirect

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
            Q(course__code__iregex=query) |
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
    # A dedicated slug field on the model would be a more performant solution.
    # Using allow_unicode=True to correctly handle non-ASCII characters.
    try:
        prof = next(p for p in Professor.objects.all() if slugify(p.name, allow_unicode=True) == slug)
    except StopIteration:
        raise Http404("Professor not found or slug could not be matched.")
    
    # Pre-fetch related data for the found professor to optimize queries
    prof = Professor.objects.prefetch_related('section_set__course', 'review_set__user').get(pk=prof.pk)
    return render(request, 'core/prof_detail.html', {'prof': prof})

def course_detail(request, slug):
    # First, try to find the course by its code (case-insensitive).
    course = Course.objects.filter(code__iexact=slug).first()

    # If not found by code, try to find it by its slugified name.
    if not course:
        try:
            # Find the first course where its slugified name matches the provided slug.
            found_by_name = next(c for c in Course.objects.all() if slugify(c.name, allow_unicode=True) == slug)
            # If found, permanently redirect to the URL with the course code.
            return HttpResponsePermanentRedirect(redirect('core:course_detail', slug=found_by_name.code).url)
        except StopIteration:
            # If not found by name either, raise a 404.
            raise Http404("Course not found.")

    # If we found the course (by code), prefetch related data and render the page.
    try:
        course = Course.objects.prefetch_related('section_set__professor', 'section_set__campus', 'section_set__room').get(pk=course.pk)
        return render(request, 'core/course_detail.html', {'course': course})
    except Course.DoesNotExist:
        raise Http404("Course not found.")