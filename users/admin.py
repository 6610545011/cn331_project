from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Extra Profile Info', {'fields': ('imgurl',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Extra Profile Info', {'fields': ('imgurl',)}),
    )
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(User, CustomUserAdmin)