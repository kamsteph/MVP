# from email.policy import default
#
# from django.db import models
# from applications.products.models import Product
# from django.conf import settings
#
# # Create your models here
# class Order(models.Model):
#     STATUS_CHOICES=[
#         ('PENDING', 'pending'),
#         ('COMPLETED', 'Completed')
#     ]
#     idUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='orders')
#     createdAt=models.DateTimeField()
#     totalPaid=models.DecimalField(max_digits=10,decimal_places=2)
#     status=models.CharField(max_length=20,choices=STATUS_CHOICES, default='PENDING')
#     totalAmount=models.DecimalField(max_digits=10,decimal_places=2)
#
#     def calculate_total(self):
#         """Returns the total amount of all the order items"""
#         total = sum(item.get_subtotal() for item in self.items.all())
#         self.totalAmount = total
#         self.save()
#         return total
#
#     def mark_as_paid(self):
#         """Updates status to COMPLETED and ensures totalPaid matches totalAmount"""
#         self.status = 'COMPLETED'
#         self.totalPaid = self.totalAmount
#         self.save()
#
# class OrderItem(models.Model):
#     priceProduct=models.DecimalField(max_digits=10,decimal_places=2)
#     qtyProduct=models.IntegerField()
#     idProduct=models.ForeignKey(Product, on_delete=models.PROTECT)
#     idOrder=models.ForeignKey(Order,on_delete=models.CASCADE,related_name ='items')
#
#     def get_subtotal(self):
#         """Returns the calculated price for this specific line item"""
#         return self.priceProduct * self.qtyProduct
#
#     def save(self, *args, **kwargs):
#         #captures the product
#         product = self.idProduct
#
#         if product.update_stock(self.qtyProduct):
#             super().save(*args,**kwargs)
#         else:
#             raise ValueError(f"Insufficient stock for {product.title}")
#
# applications/orders/models.py
import uuid
from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from applications.products.models import Product


class Order(models.Model):
    class Status(models.TextChoices):       # TextChoices > raw list of tuples (autocomplete-friendly)
        PENDING   = 'PENDING',   'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'   # added: real apps need cancellations

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(            # renamed: idUser → user
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders',
    )
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_paid   = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at  = models.DateTimeField(auto_now_add=True)   
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} — {self.user.username} [{self.status}]"

    def calculate_total(self):
        """Recalculates total from all live OrderItems and saves it."""
        total = sum(item.get_subtotal() for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])   # update_fields: only write the one column, not the whole row
        return total

    def mark_as_paid(self):
        """
        INDUSTRY UPGRADE: Wraps the status change in an atomic transaction.
        If the save() crashes halfway through, the whole thing rolls back.
        Nothing is left in a half-paid state.
        """
        with transaction.atomic():
            self.status     = self.Status.COMPLETED
            self.total_paid = self.total_amount
            self.save(update_fields=['status', 'total_paid'])


class OrderItem(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    order       = models.ForeignKey(Order,   on_delete=models.CASCADE, related_name='items')   # renamed
    product     = models.ForeignKey(Product, on_delete=models.PROTECT)                         # renamed

    # ── Denormalized / Frozen fields ──────────────────────────────────────────
    # INDUSTRY UPGRADE: price_at_purchase is written ONCE at order time and never touched again.
    # Even if the vendor changes Product.price next week, this receipt stays accurate.
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    quantity          = models.PositiveIntegerField()   # renamed + PositiveIntegerField

    def __str__(self):
        return f"{self.quantity}x {self.product.title} @ {self.price_at_purchase}"

    def get_subtotal(self):
        return self.price_at_purchase * self.quantity

    def clean(self):
        """
        INDUSTRY UPGRADE: Vendor Restriction — "Safe Buy" Rule.
        Runs before save(). Raises ValidationError (not ValueError) so
        Django forms AND DRF serializers both catch it automatically.
        """
        # Guard: make sure both sides are loaded before comparing
        if self.product_id and self.order_id:
            order_user  = self.order.user
            product_vendor = self.product.vendor

            if order_user == product_vendor:
                raise ValidationError(
                    "Vendors cannot purchase their own products."
                )

    def save(self, *args, **kwargs):
        """
        INDUSTRY UPGRADE: Everything that touches money or stock
        is wrapped in a single atomic transaction.

        If stock update succeeds but save() crashes → stock rolls back too.
        No orphaned stock deductions. No ghost orders.
        """
        with transaction.atomic():
            self.clean()   # run the Safe Buy validation before anything else

            # Freeze the price at the moment of purchase (denormalization)
            if not self.price_at_purchase:
                self.price_at_purchase = self.product.price

            # Atomic stock update (returns True only if stock was sufficient and locked)
            stock_updated = self.product.update_stock(self.quantity)
            if not stock_updated:
                raise ValidationError(f"Insufficient stock for '{self.product.title}'.")

            super().save(*args, **kwargs)

        # Recalculate the order total after the item is safely saved
        self.order.calculate_total()
