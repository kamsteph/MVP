from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False # profile lifecycle tied to user
    verbose_name_plural = 'Profile'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,) # profile edited directly inside user page

    list_display = ('username', 'email', 'get_role', 'is_active', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'profile__role')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)

    @admin.display(description='Role')
    def get_role(self, obj):
        #avoids crashes in case profile doesn't exist yet
         return obj.profile.role if hasattr(obj, 'profile') else '--'

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display =  ('user','role','store_name','is_deleted','created_at')
    list_filter = ('role','is_deleted')
    search_fields = ('user__username', 'store_name', 'tax_id')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return Profile.all_objects.all()



