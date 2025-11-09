# core/urls.py
from django.urls import path
from .views import course_detail, homepage_view, about_view, search, prof_detail

app_name = 'core'

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('about/', about_view, name='about'),
    path('search/', search, name='search'),
    path('professors/<str:slug>/', prof_detail, name='professor_detail'),
    path('courses/<str:slug>/', course_detail, name='course_detail'),
]