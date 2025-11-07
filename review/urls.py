from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('write/', views.write_review, name='write_review'),
    # path('', views.review_list, name='review_list'),
    path('ajax/search-courses/', views.search_courses, name='ajax_search_courses'),
    path('ajax/get-professors/', views.get_professors_for_course, name='ajax_get_professors'),
]