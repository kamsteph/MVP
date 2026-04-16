from django.contrib import admin
from .models import Category,Product

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display        = ('name', 'slug', 'get_product_count', 'is_deleted')
    prepopulated_fields = {'slug': ('name',)}
    search_fields       = ('name',)

    # surfaces soft-deleted categories for admins
    def get_queryset(self, request):
        return Category.all_objects.all()

    @admin.display(description='Products')
    def get_product_count(self,obj):
        return obj.get_product_count()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display    = ('title', 'vendor', 'category', 'price', 'stock', 'is_deleted')
    list_filter     = ('category', 'is_deleted')
    search_fields   = ('title', 'vendor__username')          # fixed typo: search_filed → search_fields
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return Product.all_objects.all()