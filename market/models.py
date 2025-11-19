from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


def unique_slug(base: str, model, slug_field: str = "slug") -> str:
    slug = slugify(base)[:100] or "item"
    unique = slug
    i = 1
    while model.objects.filter(**{slug_field: unique}).exists():
        i += 1
        unique = f"{slug}-{i}"
    return unique


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self.name, Category)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Prix avant promotion (optionnel)")
    stock = models.IntegerField(default=0)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="products", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.all()
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    @property
    def review_count(self):
        """Get total number of reviews"""
        return self.reviews.count()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="products/%Y/%m/%d/")
    is_primary = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="cart", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping information
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=128)
    shipping_postal_code = models.CharField(max_length=32)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase

    def __str__(self):
        return f"{self.quantity}x {self.product.name} (Order {self.order.order_number})"

    @property
    def subtotal(self):
        return self.price * self.quantity


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="reviews", on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # One review per user per product

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}: {self.subject}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Commande'),
        ('review', 'Avis'),
        ('message', 'Message'),
        ('product', 'Produit'),
        ('system', 'Système'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='favorites', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='favorited_by', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
