# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from review.models import Review, Bookmark

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {username}!")
                return redirect('core:homepage') # กลับไปหน้าแรกหลัง login สำเร็จ
            else:
                messages.error(request,"Invalid username or password.")
        else:
            messages.error(request,"Invalid username or password.")
    
    # ถ้าเป็น GET request หรือ form ไม่ผ่าน ก็แสดงหน้าฟอร์มเปล่าๆ
    form = LoginForm()
    return render(request, 'users/login.html', {'form': form})

def logout_view(request):
    """
    Logout view that handles both GET and POST requests.
    """
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')

@login_required
def profile_view(request):
    """
    แสดงหน้าโปรไฟล์ของผู้ใช้ พร้อมกับรีวิวที่เขียนและรีวิวที่บุ๊คมาร์คไว้
    """
    user = request.user

    # ดึงข้อมูลรีวิวทั้งหมดที่ผู้ใช้คนนี้เขียน
    # ใช้ select_related เพื่อลดจำนวน query ไปยัง database ทำให้เร็วขึ้น
    user_reviews = Review.objects.filter(user=user).select_related('course', 'prof').order_by('-date_created')

    # ดึงข้อมูลบุ๊คมาร์คที่เป็นรีวิว (review is not null)
    bookmarked_reviews = Bookmark.objects.filter(user=user, review__isnull=False).select_related(
        'review__course', 'review__user', 'review__prof'
    ).order_by('-id') # เรียงตามล่าสุดที่บุ๊คมาร์ค

    context = {
        'user_reviews': user_reviews,
        'bookmarked_reviews': bookmarked_reviews,
    }
    
    return render(request, 'users/profile.html', context)