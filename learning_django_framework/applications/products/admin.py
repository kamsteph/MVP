from django.contrib import admin
from .models import Category,Product

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['nameCategory', 'slug']
    prepopulated_fields = {'slug': ('nameCategory',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'price','stock','idUser']
    search_filed=['title']