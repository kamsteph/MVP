from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title','price','stock','idCategory','image','description']

    def clean_price(self):
       price = self.cleaned_data.get('price')

       if price is not None and price <= 0:
           raise forms.ValidationError("Le prix doit être supérieur à zéro")
       return price

    def clean_stock(self):
       stock = self.cleaned_data.get('stock')

       if stock is not None and stock < 0:
           raise forms.ValidationError("La quantité en inventaire ne peut pas être négative")
       return stock
