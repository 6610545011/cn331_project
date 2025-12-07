# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, ChangeImageForm
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

@login_required
def profile_view(request):
    """
    แสดงหน้าโปรไฟล์ของผู้ใช้ พร้อมกับรีวิวที่เขียนและรีวิว/คอร์สที่บุ๊คมาร์คไว้
    """
    user = request.user

    # ดึงข้อมูลรีวิวทั้งหมดที่ผู้ใช้คนนี้เขียน
    # ใช้ select_related เพื่อลดจำนวน query ไปยัง database ทำให้เร็วขึ้น
    user_reviews = Review.objects.filter(user=user).select_related('course', 'prof').order_by('-date_created')

    # ดึงข้อมูลบุ๊คมาร์คที่เป็นรีวิว (review is not null)
    bookmarked_reviews = Bookmark.objects.filter(user=user, review__isnull=False).select_related(
        'review__course', 'review__user', 'review__prof'
    ).order_by('-id')
    
    # ดึงข้อมูลบุ๊คมาร์คที่เป็นคอร์ส (review is null)
    bookmarked_courses = Bookmark.objects.filter(user=user, review__isnull=True).select_related(
        'course'
    ).order_by('-id')

    context = {
        'user_reviews': user_reviews,
        'bookmarked_reviews': bookmarked_reviews,
        'bookmarked_courses': bookmarked_courses,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile_view(request):
    """
    Edit user profile, including changing the profile image URL
    """
    user = request.user
    
    if request.method == 'POST':
        form = ChangeImageForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile image updated successfully!")
            return redirect('users:profile')
        else:
            messages.error(request, "Please enter a valid image URL.")
    else:
        form = ChangeImageForm(instance=user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'users/edit_profile.html', context)