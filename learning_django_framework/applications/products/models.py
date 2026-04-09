from django.db import models
from django.conf import settings

from django.template.defaultfilters import slugify


# Create your models here.
class Product(models.Model):
    idUser=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    idCategory=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='products')
    title=models.CharField(max_length=255)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    image=models.CharField(max_length=255)
    stock=models.IntegerField()
    description=models.CharField(max_length=255)
    slug = models.SlugField(unique=True,blank=True)

    def is_in_stock(self):
        """Returns True if stock is greater than zero"""
        return self.stock > 0

    def update_stock(self, quantity_sold):
        """updates the available within the shelf"""
        if self.stock >= quantity_sold:
            self.stock -= quantity_sold
            self.save()
            return True
        return False

    def save(self,*args,**kwargs): #generate_slug method in class diagram
        """Generates slug for unique name pattern in url"""
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args,**kwargs)

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    def get_product_count(self):
        """Counts the amount of product"""
        return self.products.count()


