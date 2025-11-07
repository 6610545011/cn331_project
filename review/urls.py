from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('write/', views.write_review, name='write_review'),
    # path('', views.review_list, name='review_list'),
]