# users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # URL สำหรับหน้า Login
    path('login/', views.login_view, name='login'),
    
    # URL สำหรับ Logout (ใช้ View สำเร็จรูปของ Django)
    path('logout/', auth_views.LogoutView.as_view(next_page='core:homepage'), name='logout'),
]