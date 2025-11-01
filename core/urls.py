# core/urls.py
from django.urls import path
from .views import homepage_view, about_view # <-- import about_view

app_name = 'core'

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('about/', about_view, name='about'), # <-- เพิ่มบรรทัดนี้
]