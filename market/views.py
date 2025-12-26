from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta

from .models import (
    Category, Product, ProductImage, Cart, CartItem,
    Order, OrderItem, Review, Message, Notification
)
from .serializers import (
    CategorySerializer, ProductSerializer, ProductImageSerializer,
    CartSerializer, CartItemSerializer, OrderSerializer, OrderCreateSerializer,
    OrderItemSerializer, ReviewSerializer, MessageSerializer, NotificationSerializer,
    FavoriteSerializer
)
from .permissions import IsOwnerOrReadOnly, IsSellerOrReadOnly, IsOrderOwner, IsMessageParticipant


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {"name": ["exact", "icontains"], "slug": ["exact", "icontains"]}
    search_fields = ["name", "slug"]
    ordering_fields = ["name"]


from rest_framework.parsers import MultiPartParser, FormParser

class ProductViewSet(viewsets.ModelViewSet):
    parser_classes = (MultiPartParser, FormParser)
    queryset = Product.objects.select_related("category", "owner").prefetch_related("images", "reviews").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "category": ["exact"],
        "owner": ["exact"],
        "is_active": ["exact"],
        "price": ["gte", "lte"],
        "stock": ["gte", "lte"],
    }
    search_fields = ["name", "description"]
    ordering_fields = ["-created_at", "price", "name", "stock"]

    def perform_create(self, serializer):
        product = serializer.save(owner=self.request.user)
        
        # Handle uploaded images
        images = self.request.FILES.getlist('uploaded_images')
        for image in images:
            ProductImage.objects.create(product=product, image=image)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a product"""
        product = self.get_object()
        reviews = product.reviews.all()
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get('product', None)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        return queryset


class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related('items__product')

    def get_object(self):
        """Get or create cart for current user"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Produit non trouvé"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check stock
        if product.stock < quantity:
            return Response(
                {"error": "Stock insuffisant"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create cart item
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        cart = Cart.objects.get(user=request.user)
        item_id = request.data.get('item_id')

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Article non trouvé dans le panier"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_quantity(self, request):
        """Update item quantity in cart"""
        cart = Cart.objects.get(user=request.user)
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            
            # Check stock
            if cart_item.product.stock < quantity:
                return Response(
                    {"error": "Stock insuffisant"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item.quantity = quantity
            cart_item.save()
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Article non trouvé dans le panier"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear all items from cart"""
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwner]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'profile') and user.profile.is_seller:
            # Sellers can see orders containing their products
            return Order.objects.filter(
                Q(user=user) | Q(items__product__owner=user)
            ).distinct().prefetch_related('items__product')
        return Order.objects.filter(user=user).prefetch_related('items__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status (seller only)"""
        order = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason')

        # Check if user is seller of products in this order
        user_products = request.user.products.values_list('id', flat=True)
        order_product_ids = order.items.values_list('product_id', flat=True)
        
        if not any(pid in user_products for pid in order_product_ids):
            return Response(
                {"error": "Non autorisé"},
                status=status.HTTP_403_FORBIDDEN
            )

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            
            # Create notification for buyer
            message = f"Votre commande est maintenant: {order.get_status_display()}"
            if reason:
                message += f". Motif: {reason}"
            Notification.objects.create(
                user=order.user,
                title=f"Commande {order.order_number} mise à jour",
                message=message,
                notification_type='order'
            )
            
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        
        return Response(
            {"error": "Statut invalide"},
            status=status.HTTP_400_BAD_REQUEST
        )


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["product", "rating"]
    ordering_fields = ["-created_at", "rating"]

    def update(self, request, *args, **kwargs):
        """Restrict update to review owner"""
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        review = serializer.save(user=self.request.user)
        
        # Create notification for product owner
        Notification.objects.create(
            user=review.product.owner,
            title="Nouvel avis sur votre produit",
            message=f"{self.request.user.username} a laissé un avis sur {review.product.name}",
            notification_type='review'
        )

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """Seller response to a review"""
        review = self.get_object()
        if review.product.owner != request.user:
            return Response({"detail": "Non autorisé"}, status=status.HTTP_403_FORBIDDEN)
        response_text = request.data.get('response', '').strip()
        if not response_text:
            return Response({"detail": "Réponse requise"}, status=status.HTTP_400_BAD_REQUEST)
        review.response = response_text
        review.response_at = timezone.now()
        review.save()
        serializer = ReviewSerializer(review)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, IsMessageParticipant]
    filter_backends = [OrderingFilter]
    ordering_fields = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        inbox = self.request.query_params.get('inbox', None)
        
        if inbox == 'sent':
            return Message.objects.filter(sender=user)
        elif inbox == 'received':
            return Message.objects.filter(receiver=user)
        
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))

    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # Create notification for receiver
        Notification.objects.create(
            user=message.receiver,
            title="Nouveau message",
            message=f"{self.request.user.username}: {message.subject}",
            notification_type='message'
        )

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        message.is_read = True
        message.save()
        serializer = MessageSerializer(message)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_read", "notification_type"]
    ordering_fields = ["-created_at"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().update(is_read=True)
        return Response({"status": "Toutes les notifications sont marquées comme lues"})


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = ["-created_at"]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('product')

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Toggle favorite status for a product"""
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            favorite = Favorite.objects.get(user=request.user, product_id=product_id)
            favorite.delete()
            return Response({"status": "removed", "is_favorite": False})
        except Favorite.DoesNotExist:
            Favorite.objects.create(user=request.user, product_id=product_id)
            return Response({"status": "added", "is_favorite": True})


# Seller Statistics Views
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class SellerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get seller statistics"""
        user = request.user
        
        if not (hasattr(user, 'profile') and user.profile.is_seller):
            return Response(
                {"error": "Utilisateur non vendeur"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get date range (default: this month)
        today = timezone.now()
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate statistics
        products = user.products.all()
        
        # Orders containing seller's products
        orders = Order.objects.filter(
            items__product__owner=user,
            created_at__gte=start_date
        ).distinct()
        
        # Sales this month
        sales_this_month = OrderItem.objects.filter(
            product__owner=user,
            order__created_at__gte=start_date,
            order__status='delivered'
        ).aggregate(
            total=Sum('price')
        )['total'] or 0
        
        # Active orders
        active_orders = orders.exclude(status='delivered').count()
        
        # Total products
        total_products = products.count()
        
        # Total customers (unique users who ordered)
        total_customers = Order.objects.filter(
            items__product__owner=user
        ).values('user').distinct().count()

        # Daily sales for the last 7 days (for chart)
        daily_sales = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            day_name = date.strftime('%a') # Mon, Tue, etc.
            day_sales = OrderItem.objects.filter(
                product__owner=user,
                order__created_at__date=date.date(),
                order__status='delivered'
            ).aggregate(total=Sum('price'))['total'] or 0
            daily_sales.append({'name': day_name, 'sales': float(day_sales)})
        
        stats = {
            'sales_this_month': float(sales_this_month),
            'active_orders': active_orders,
            'total_products': total_products,
            'total_customers': total_customers,
            'daily_sales': daily_sales,
            'products': ProductSerializer(products[:5], many=True, context={'request': request}).data,
            'recent_orders': OrderSerializer(orders[:5], many=True, context={'request': request}).data,
        }
        
        return Response(stats)


class DeliveryFeeView(APIView):
    permission_classes = [IsAuthenticated]

    BASE_LATITUDE = 12.5
    BASE_LONGITUDE = -1.5

    def post(self, request):
        latitude = self._parse_float(request.query_params.get("latitude") or request.data.get("latitude"))
        longitude = self._parse_float(request.query_params.get("longitude") or request.data.get("longitude"))

        if latitude is None or longitude is None:
            return Response(
                {"detail": "Latitude et longitude requises"},
                status=status.HTTP_400_BAD_REQUEST
            )

        distance_km = self._approx_distance(latitude, longitude)
        fee = 500 + distance_km * 50

        return Response({
            "fee": round(fee),
            "currency": "FCFA",
            "distance_km": round(distance_km, 2),
        })

    def _parse_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _approx_distance(self, lat, lon):
        lat_diff = abs(lat - self.BASE_LATITUDE)
        lon_diff = abs(lon - self.BASE_LONGITUDE)
        return ((lat_diff ** 2) + (lon_diff ** 2)) ** 0.5 * 111
