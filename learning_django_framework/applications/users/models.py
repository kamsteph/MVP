import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    email=models.CharField(max_length=100)
    isVendor=models.BooleanField(default=False)
    isCustomer=models.BooleanField(default=False)
    dateJoined=models.DateTimeField()

#No need for adding password field since it is inherited from Abstract User
def get_full_name(self):
    """Returns the full name of the user"""
    return self.username

def get_active_orders(self):
    """Returns the list of orders which are still active"""
