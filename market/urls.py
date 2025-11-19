from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    CategoryViewSet, ProductViewSet, ProductImageViewSet,
    CartViewSet, OrderViewSet, ReviewViewSet,
    MessageViewSet, NotificationViewSet, SellerStatsView
)


router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='productimage')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('seller/stats/', SellerStatsView.as_view(), name='seller-stats'),
] + router.urls
