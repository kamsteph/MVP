from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Register your models here.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Marketplace Role', {'fields': ('is_vendor', 'is_customer')}),
    )
    list_display = ['username', 'email', 'is_vendor', 'is_staff']