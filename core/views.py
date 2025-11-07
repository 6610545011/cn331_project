# core/views.py
from django.shortcuts import render
from django.db.models import Q

from .models import Professor, Course, Section

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