from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    phone = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=128, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    
    # Seller information
    is_seller = models.BooleanField(default=False)
    business_name = models.CharField(max_length=200, blank=True)
    business_description = models.TextField(blank=True)
    business_address = models.CharField(max_length=255, blank=True)
    business_city = models.CharField(max_length=128, blank=True)
    business_postal_code = models.CharField(max_length=32, blank=True)
    
    # Stats (calculated fields)
    total_sales = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Profil de {self.user}"
    
    @property
    def seller_rating(self):
        """Calculate average rating from all product reviews"""
        from market.models import Review
        product_ids = self.user.products.values_list('id', flat=True)
        reviews = Review.objects.filter(product_id__in=product_ids)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created and not hasattr(instance, "profile"):
        UserProfile.objects.create(user=instance)
