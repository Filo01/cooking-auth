from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as UserAdminDjango
from .models import User


@admin.register(User)
class UserAdmin(UserAdminDjango):
    pass
