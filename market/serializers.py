from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, Review, Message, Notification
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]
        extra_kwargs = {"slug": {"required": False}}


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary", "order", "created_at"]
        read_only_fields = ["created_at"]


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ["id", "product", "user", "username", "rating", "comment", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "stock",
            "category",
            "category_name",
            "owner",
            "owner_name",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "average_rating",
            "review_count",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal", "added_at"]
        read_only_fields = ["added_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_items", "total_price", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            "id",
            "user",
            "order_number",
            "status",
            "status_display",
            "total_amount",
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "order_number", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders from cart"""
    
    class Meta:
        model = Order
        fields = [
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        cart = Cart.objects.get(user=user)
        
        if not cart.items.exists():
            raise serializers.ValidationError("Le panier est vide")
        
        # Calculate total
        total_amount = cart.total_price
        
        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            **validated_data
        )
        
        # Create order items from cart
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Clear cart
        cart.items.all().delete()
        
        return order


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.StringRelatedField(read_only=True)
    receiver = serializers.StringRelatedField(read_only=True)
    sender_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='sender',
        write_only=True,
        required=False
    )
    receiver_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='receiver',
        write_only=True
    )
    
    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "receiver",
            "sender_id",
            "receiver_id",
            "subject",
            "body",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            "id",
            "user",
            "title",
            "message",
            "notification_type",
            "notification_type_display",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]
