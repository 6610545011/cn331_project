from django import forms
from django.contrib.auth.forms import AuthenticationForm
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
