from django.db import models
from applications.products.models import Product
from enum import Enum

# Create your models here.
status = Enum('status',[('PENDING',1),('COMPLETED',2)])
class Order(models.Model):
    createdAt=models.DateTimeField()
    totalPaid=models.DecimalField(max_digits=10,decimal_places=2)
    status=models.CharField(max_length=20,default='PENDING')
    totalAmount=models.DecimalField(max_digits=10,decimal_places=2)

class OrderItem(models.Model):
    priceProduct=models.DecimalField(max_digits=10,decimal_places=2)
    qtyProduct=models.IntegerField()
    idProduct=models.ForeignKey(Product, on_delete=models.CASCADE)
    idOrder=models.ForeignKey(Order,on_delete=models.CASCADE)

def get_subtotal(self):
    """Returns the calculated price for this specific line item"""
    return self.priceProduct * self.qtyProduct

def calculate_total(self):
    """Returns the total amount of all the order items"""

def mark_as_paid(self):
    """Tells whether the transaction is paid or not"""

