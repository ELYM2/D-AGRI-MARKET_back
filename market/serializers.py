from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, SubOrder, Review, Message, Notification, Favorite
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
    response = serializers.CharField(required=False, allow_blank=True)
    response_at = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = Review
        fields = ["id", "product", "user", "username", "rating", "comment", "response", "response_at", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at", "response", "response_at"]


class ProductSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    review_count = serializers.IntegerField(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "old_price",
            "stock",
            "unit",
            "category",
            "category_name",
            "owner",
            "owner_name",
            "is_active",
            "created_at",
            "updated_at",
            "images",
            "average_rating",
            "average_rating",
            "review_count",
            "is_favorite",
        ]
        read_only_fields = ["owner", "created_at", "updated_at", "average_rating", "review_count", "is_favorite"]

    def get_is_favorite(self, obj):
        try:
            request = self.context.get('request')
            if request and request.user.is_authenticated:
                return Favorite.objects.filter(user=request.user, product=obj).exists()
        except Exception:
            pass
        return False


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "added_at"]
        read_only_fields = ["added_at"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_items", "total_price", "created_at", "updated_at"]
        read_only_fields = ["user", "created_at", "updated_at"]
    
    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())
    
    def get_total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_name", "quantity", "price"]
        read_only_fields = ["price"]


class SubOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    user_name = serializers.CharField(source='order.user.username', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    shipping_city = serializers.CharField(source='order.shipping_city', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SubOrder
        fields = [
            "id",
            "order_number",
            "user_name",
            "seller_name",
            "status",
            "status_display",
            "subtotal",
            "shipping_city",
            "items",
            "created_at"
        ]
        read_only_fields = ["order_number", "user_name", "subtotal", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    sub_orders = SubOrderSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "user_name",
            "status",
            "status_display",
            "total_amount",
            "shipping_address",
            "shipping_city",
            "shipping_postal_code",
            "items",
            "sub_orders",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "order_number", "total_amount", "created_at", "updated_at"]


class OrderCreateSerializer(serializers.Serializer):
    shipping_address = serializers.CharField(max_length=500)
    shipping_city = serializers.CharField(max_length=100)
    shipping_postal_code = serializers.CharField(max_length=20)

    def create(self, validated_data):
        user = self.context['request'].user
        
        # Get user's cart
        try:
            cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Votre panier est vide")
            
        if not cart.items.exists():
            raise serializers.ValidationError("Votre panier est vide")

        # Calculate total and check stock
        total_amount = 0
        items_by_seller = {}

        for item in cart.items.all():
            if item.product.stock < item.quantity:
                raise serializers.ValidationError(f"Stock insuffisant pour {item.product.name}")
            
            total_amount += item.product.price * item.quantity
            
            # Group by seller
            owner = item.product.owner
            if owner not in items_by_seller:
                items_by_seller[owner] = []
            items_by_seller[owner].append(item)

        # Create Parent Order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_address=validated_data['shipping_address'],
            shipping_city=validated_data['shipping_city'],
            shipping_postal_code=validated_data['shipping_postal_code']
        )

        # Create SubOrders and OrderItems
        for owner, items in items_by_seller.items():
            sub_total = sum(item.product.price * item.quantity for item in items)
            
            sub_order = SubOrder.objects.create(
                order=order,
                seller=owner,
                subtotal=sub_total,
                status='pending'
            )

            for item in items:
                OrderItem.objects.create(
                    order=order,
                    sub_order=sub_order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # Decrement stock
                item.product.stock -= item.quantity
                item.product.save()
            
            # Create notification for seller
            if owner != user:
                Notification.objects.create(
                    user=owner,
                    title="Nouvelle commande",
                    message=f"Vous avez reçu une nouvelle commande de {sub_total} FCFA (Cmd #{order.order_number})",
                    notification_type='order'
                )

        # Clear cart
        cart.items.all().delete()
        
        # Create notification for buyer
        Notification.objects.create(
            user=user,
            title="Commande confirmée",
            message=f"Votre commande #{order.order_number} a été enregistrée avec succès.",
            notification_type='order'
        )
        
        return order






class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            "id",
            "product",
            "product_name",
            "user",
            "user_name",
            "rating",
            "comment",
            "response",
            "response_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "response", "response_at", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    receiver_name = serializers.CharField(source='receiver.username', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_name",
            "receiver",
            "receiver_name",
            "subject",
            "body",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["sender", "created_at"]


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
            "link",
            "created_at",
        ]
        read_only_fields = ["user", "created_at"]


class FavoriteSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Favorite
        fields = ["id", "product", "product_id", "created_at"]
        read_only_fields = ["id", "created_at"]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
