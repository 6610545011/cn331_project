# core/urls.py
from django.urls import path, register_converter
from .views import course_detail, homepage_view, about_view, search, prof_detail
from .converters import CaseInsensitiveSlugConverter

register_converter(CaseInsensitiveSlugConverter, 'ci')

app_name = 'core'

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('about/', about_view, name='about'),
    path('search/', search, name='search'),
    path('professors/<int:pk>/', prof_detail, name='professor_detail'),
    path('courses/<ci:course_code>/', course_detail, name='course_detail'),
]