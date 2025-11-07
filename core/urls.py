# core/urls.py
from django.urls import path
from .views import homepage_view, about_view, search  # <-- re-add search import

app_name = 'core'

urlpatterns = [
    path('', homepage_view, name='homepage'),
    path('about/', about_view, name='about'),
    path('search/', search, name='search'),
]