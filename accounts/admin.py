from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'status', 'is_staff', 'is_active')
    list_filter = ('role', 'status', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'phone', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('RESQ Specific', {'fields': ('role', 'phone', 'status')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('RESQ Specific', {'fields': ('role', 'phone', 'status')}),
    )
