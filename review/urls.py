# review/urls.py

from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('write/', views.write_review, name='write_review'),
    path('vote/<int:review_id>/', views.vote_review, name='vote_review'),
    path('bookmark/toggle/<int:review_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('report/<int:review_id>/', views.report_review, name='report_review'),

    # AJAX URLs
    path('ajax/search-courses/', views.ajax_search_courses, name='ajax_search_courses'),
    path('ajax/get-professors/', views.ajax_get_professors, name='ajax_get_professors'),
    path('ajax/get-sections/', views.ajax_get_sections_for_course, name='ajax_get_sections_for_course'),
]