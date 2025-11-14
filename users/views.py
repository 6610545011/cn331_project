# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import EmailAuthenticationForm
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=email, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"Welcome back, {email}!")
                return redirect('core:homepage') # กลับไปหน้าแรกหลัง login สำเร็จ
            else:
                messages.error(request,"Invalid email or password.")
        else:
            messages.error(request,"Invalid email or password.")
    
    # ถ้าเป็น GET request หรือ form ไม่ผ่าน ก็แสดงหน้าฟอร์มเปล่าๆ
    form = EmailAuthenticationForm()
    return render(request, 'users/login.html', {'form': form})