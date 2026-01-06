from django.urls import path
from .views import (
    SellerListView,
    SellerDetailView,
)

urlpatterns = [
    path('', SellerListView.as_view(), name='seller-list'),
    path('<int:pk>/', SellerDetailView.as_view(), name='seller-detail'),
]

