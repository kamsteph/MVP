from email.policy import default

from django.db import models
from applications.products.models import Product
from enum import Enum

# Create your models here
class Order(models.Model):
    STATUS_CHOICES=[
        ('PENDING', 'pending'),
        ('COMPLETED', 'Completed')
    ]
    createdAt=models.DateTimeField()
    totalPaid=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=20,choices=STATUS_CHOICES, default='PENDING')
    totalAmount=models.DecimalField(max_digits=10,decimal_places=2)

    def calculate_total(self):
        """Returns the total amount of all the order items"""
        total = sum(item.get_subtotal() for item in self.items.all())
        self.totalAmount = total
        self.save()
        return total

    def mark_as_paid(self):
        """Updates status to COMPLETED and ensures totalPaid matches totalAmount"""
        self.status = 'COMPLETED'
        self.totalPaid = self.totalAmount
        self.save()

class OrderItem(models.Model):
    priceProduct=models.DecimalField(max_digits=10,decimal_places=2)
    qtyProduct=models.IntegerField()
    idProduct=models.ForeignKey(Product, on_delete=models.CASCADE)
    idOrder=models.ForeignKey(Order,on_delete=models.CASCADE,related_name ='items')

    def get_subtotal(self):
        """Returns the calculated price for this specific line item"""
        return self.priceProduct * self.qtyProduct

