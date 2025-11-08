# core/views.py
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.utils.text import slugify
from .models import Professor, Course, Section
from django.http import Http404

def homepage_view(request):
    return render(request, 'core/homepage.html')

# เพิ่มฟังก์ชันนี้เข้าไป
def about_view(request):
    return render(request, 'core/about.html')

def search(request):
    query = request.GET.get('q', '')

    if query:
        professors = Professor.objects.filter(
            Q(name__icontains=query)
        )
        courses = Course.objects.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query)
        )
        sections = Section.objects.filter(
            Q(course__name__icontains=query)
        )
    else:
        professors = []  # or any other default value you want
        courses = []  # or any other default value you want
        sections = []

    context = {
        'query': query,
        'professors': professors,
        'courses': courses,
        'sections': sections,
    }
    return render(request, 'core/search.html', context)



def prof_detail(request, slug):

    for prof in Professor.objects.all():
        if slugify(prof.name) == slug:
            return render(request, 'core/prof_detail.html', {'prof': prof})
    raise Http404("Professor not found")

def course_detail(request, slug):

    for course in Course.objects.all():
        if slugify(course.name) == slug:
            return render(request, 'core/course_detail.html', {'course': course})
    raise Http404("Course not found")