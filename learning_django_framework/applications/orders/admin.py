from django.contrib import admin
from .models import Order,OrderItem

# Register your models here.
@admin.register(Order)
class OrderAdmin(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'createdAt', 'status', 'totalAmount']
    inlines = [OrderItemInline]
