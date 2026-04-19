from django import forms
from .models import Product
from .utils.image_processors import resize_image

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title','price','stock','category','image','description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}), # renders a textarea
            'price': forms.NumberInput(attrs={'min': '0.01'}),
            'stock': forms.NumberInput(attrs={'min':'0'})
        }

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

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            allowed_types = ['image/jpeg', 'image/png', 'image/webp']
            if image.content_type not in allowed_types:
                raise forms.ValidationError("Format accepté : JPEG,PNG, WEBP uniquement.")

            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("L'image ne doit pas dépasser 5MB")
        return image

    def save(self, commit = True):
        instance = super().save(commit=False) # build the model object without hitting the DB
        if commit:
            instance.save()
            if instance.image:
                resize_image(instance.image.path)

        return instance
