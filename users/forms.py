from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from .models import User

class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={'autofocus': True, 'class': 'form-control'})
    )

class ChangeImageForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['imgurl']
        widgets = {
            'imgurl': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter image URL',
                'required': False
            })
        }
        labels = {
            'imgurl': 'Image URL'
        }

class CustomUserCreationForm(UserCreationForm):
    # --- เพิ่ม help_text ตรงนี้ครับ ---
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
        strip=False,
        # ใส่ข้อความแนะนำที่นี่ (รองรับ HTML tag เช่น <ul> <li>)
        help_text=(
            "<ul>"
            "<li>Your password can’t be too similar to your other personal information.</li>"
            "<li>Your password must contain at least 8 characters.</li>"
            "<li>Your password can’t be a commonly used password.</li>"
            "<li>Your password can’t be entirely numeric.</li>"
            "</ul>"
        )
    )
    password2 = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput,
        strip=False,
        help_text="Enter the same password as before, for verification."
    )

    class Meta:
        model = User
        fields = ('username', 'email')

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'imgurl')