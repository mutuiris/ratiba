"""Admin configuration for the accounts app"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
