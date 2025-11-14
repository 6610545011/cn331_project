# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import LoginForm

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