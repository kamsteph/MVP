# applications/products/models.py
import uuid
from django.db import models
from django.conf import settings
from django.template.defaultfilters import slugify
from django.db.models import F
from applications.users.models import SoftDeleteMixin  # reuse your mixin


class Category(SoftDeleteMixin):
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_product_count(self):
        """Counts only active (non-deleted) products in this category."""
        return self.products.count()   # SoftDeleteManager filters deleted ones


class Product(SoftDeleteMixin):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    vendor      = models.ForeignKey(                   # renamed: idUser → vendor (clearer intent)
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        limit_choices_to={'profile__role': 'VENDOR'},  # DB-level guard: only vendors own products
    )
    category    = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,                      # PROTECT: can't delete a category that has products
        related_name='products',
        null=True, blank=True,
    )

    # ── Fields ────────────────────────────────────────────────────────────────
    title       = models.CharField(max_length=255)
    price       = models.DecimalField(max_digits=10, decimal_places=2)
    image       = models.ImageField(upload_to='products/')  # ImageField > CharField for files
    stock       = models.PositiveIntegerField()              # PositiveIntegerField: stock can't go negative at DB level
    description = models.TextField()                         # TextField > CharField for long text
    slug        = models.SlugField(unique=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def is_in_stock(self):
        return self.stock > 0

    def update_stock(self, quantity_sold):
        """
        INDUSTRY UPGRADE: Atomic stock update using F() + select_for_update().

        OLD WAY (Race Condition risk):
            self.stock -= quantity_sold   ← Python reads stock, subtracts, writes back.
            self.save()                   ← If 2 users hit this at the same ms, both read
                                            stock=1, both subtract, both save stock=0. Bug!

        NEW WAY (Database-level lock):
            select_for_update() locks the row in the DB until this transaction finishes.
            F('stock') tells the DB to do the subtraction itself — never touches Python memory.
            No two requests can ever race on the same row.
        """
        updated_rows = (
            Product.objects
            .select_for_update()                        # lock this row until transaction ends
            .filter(pk=self.pk, stock__gte=quantity_sold)  # only update if stock is sufficient
            .update(stock=F('stock') - quantity_sold)   # DB does the math, not Python
        )
        # update() returns the number of rows it actually changed (1 = success, 0 = not enough stock)
        return updated_rows == 1

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)