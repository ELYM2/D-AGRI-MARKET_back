from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    CategoryViewSet, ProductViewSet, ProductImageViewSet,
    CartViewSet, OrderViewSet, ReviewViewSet,
    MessageViewSet, NotificationViewSet, SellerStatsView,
    FavoriteViewSet, DeliveryFeeView, SellerOrderViewSet
)


router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='productimage')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'seller-orders', SellerOrderViewSet, basename='seller-order')  # New endpoint
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('seller/stats/', SellerStatsView.as_view(), name='seller-stats'),
    path('seller-stats/', SellerStatsView.as_view(), name='seller-stats-legacy'),
    path('cart/calculate_delivery_fee/', DeliveryFeeView.as_view(), name='calculate-delivery-fee'),
] + router.urls
