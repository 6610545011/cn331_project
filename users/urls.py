# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # URL สำหรับหน้า Login
    path('login/', views.login_view, name='login'),
    
    # URL สำหรับ Logout (custom view ที่ handle GET requests)
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
]