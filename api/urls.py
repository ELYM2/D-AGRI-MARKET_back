from django.urls import path
from . import views


urlpatterns = [
    path('health/', views.health, name='api-health'),
    path('payments/mobile/', views.mobile_payment, name='mobile-payment'),
]
