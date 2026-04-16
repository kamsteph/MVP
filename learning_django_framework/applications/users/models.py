# import uuid
# from django.contrib.auth.models import AbstractUser
# from django.db import models
#
# # Create your models here.
# class User(AbstractUser):
#     id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
#     email=models.CharField(max_length=100)
#     isVendor=models.BooleanField(default=False)
#     isCustomer=models.BooleanField(default=False)
#
# #No need for adding password field since it is inherited from Abstract User
#     def get_full_name(self):
#         """Returns the full name of the user"""
#         return self.username
#
#     def get_active_orders(self):
#         """Returns the list of orders which are still active"""
#
#         return self.orders.filter(status='PENDING')

# applications/users/models.py
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


# ──────────────────────────────────────────────
# SOFT DELETE MIXIN  (used by ALL models)
# ──────────────────────────────────────────────
class SoftDeleteManager(models.Manager):
    """Default manager — excludes soft-deleted rows from every query."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class SoftDeleteMixin(models.Model):
    """
    Inherit this on any model to get soft-delete behaviour.
    Nothing is ever hard-deleted — rows are hidden by setting is_deleted=True.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects     = SoftDeleteManager()   # default: hides deleted rows
    all_objects = models.Manager()      # escape hatch: shows everything

    class Meta:
        abstract = True                 # not a real table — just a blueprint(mixin)

    def delete(self, *args, **kwargs):
        """Soft delete — marks the row as deleted instead of removing it."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        """Undo a soft delete."""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])

    def hard_delete(self, *args, **kwargs):
        """Permanent delete — only use for GDPR wipe requests."""
        super().delete(*args, **kwargs)


# ──────────────────────────────────────────────
# USER  (Auth only — stays lean for fast logins)
# ──────────────────────────────────────────────
class User(AbstractUser):
    """
    Lean auth table — only identity & login fields live here.
    Role/business data lives in Profile so login queries stay fast.

    KEPT from your code:  UUID pk, email, get_active_orders()
    REMOVED from here:    isVendor, isCustomer  → moved to Profile.role
    UPGRADED:             email → EmailField, get_full_name() fixed
    """
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=100, unique=True)   # EmailField validates format

    # isVendor / isCustomer intentionally removed here — see Profile below

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Returns full name, falls back to username if names aren't set."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def get_active_orders(self):
        """Returns orders that are still pending — same as your original."""
        return self.orders.filter(status='PENDING')

    # ── Role shortcuts (reads from Profile — no extra import needed in views) ──
    @property
    def is_vendor(self):
        """True if this user's profile role is VENDOR."""
        return hasattr(self, 'profile') and self.profile.role == Profile.Role.VENDOR

    @property
    def is_customer(self):
        """True if this user's profile role is CUSTOMER."""
        return hasattr(self, 'profile') and self.profile.role == Profile.Role.CUSTOMER


# ──────────────────────────────────────────────
# PROFILE  (Role & business data lives here)
# ──────────────────────────────────────────────
class Profile(SoftDeleteMixin):
    """
    One-to-One extension of User.

    WHY SEPARATE?
    - Login queries only hit the User table (fast).
    - Vendor-specific columns (store_name, tax_id) don't bloat every row.
    - Soft-deleting a Profile suspends the account without destroying auth history.

    INTEGRATES WITH:
    - Product.vendor → only users whose profile.role == VENDOR can own products.
    - OrderItem.clean() → checks order.user == product.vendor using is_vendor property.
    """

    class Role(models.TextChoices):
        VENDOR   = 'VENDOR',   'Vendor'
        CUSTOMER = 'CUSTOMER', 'Customer'
        ADMIN    = 'ADMIN',    'Admin'

    # ── Relationships ─────────────────────────────────────────────────────────
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    # ── Role ──────────────────────────────────────────────────────────────────
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CUSTOMER,
    )

    # ── Vendor-only fields (null/blank for customers) ─────────────────────────
    store_name = models.CharField(max_length=255, blank=True, null=True)
    tax_id     = models.CharField(max_length=100, blank=True, null=True)

    # ── Shared profile fields ─────────────────────────────────────────────────
    phone      = models.CharField(max_length=20, blank=True, null=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} — {self.role}"

    def is_profile_complete(self):
        """
        Vendors must have a store_name before listing products.
        Views can call this to gate the 'Add Product' page.
        """
        if self.role == self.Role.VENDOR:
            return bool(self.store_name)
        return True


# ──────────────────────────────────────────────
# SIGNALS — auto-create Profile on User creation
# ──────────────────────────────────────────────
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Fires automatically after every new User row is saved.
    Means you never have to manually call Profile.objects.create() in views.
    """
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Keeps Profile in sync whenever the User row is updated."""
    if hasattr(instance, 'profile'):
        instance.profile.save()