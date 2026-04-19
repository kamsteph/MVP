from django.contrib import admin
from .models import Order,OrderItem

# Register your models here.
# This allows edition of OrderItems directly inside the Order page (admin.TabularInline)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # no blank rows - prevents accidental empty saves
    readonly_fields = ('price_at_purchase','get_subtotal')
    fields = ('product','quantity','price_at_purchaise','get_subtotal')

    @admin.display(description='Subtotal')
    def get_subtotal(self, obj):
        return obj.get_subtotal()

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display    = ('id', 'user', 'status', 'total_amount', 'total_paid', 'created_at')
    list_filter     = ('status', 'created_at')
    search_fields   = ('user__username', 'id')
    readonly_fields = ('total_amount', 'total_paid', 'created_at', 'updated_at')  # financial fields are immutable
    inlines         = (OrderItemInline,)
    ordering        = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display    = ('order', 'product', 'quantity', 'price_at_purchase', 'get_subtotal')
    search_fields   = ('product__title', 'order__id')
    readonly_fields = ('price_at_purchase',)

    @admin.display(description='Subtotal')
    def get_subtotal(self, obj):
        return obj.get_subtotal()