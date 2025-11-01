# core/views.py
from django.shortcuts import render

def homepage_view(request):
    return render(request, 'core/homepage.html')

# เพิ่มฟังก์ชันนี้เข้าไป
def about_view(request):
    return render(request, 'core/about.html')