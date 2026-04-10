from django.contrib import admin
from .models import Order,OrderItem

# Register your models here.
# This allows edition of OrderItems directly inside the Order page (admin.TabularInline)

class OrderItemInLine(admin.TabularInline):
    model = OrderItem
    extra = 1

@admin.register(Order)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'createdAt', 'status', 'totalAmount']
    inlines = [OrderItemInLine]
