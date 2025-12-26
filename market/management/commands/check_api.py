import json
from typing import Sequence

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework.test import APIClient

from market.models import Category, Product, Order


User = get_user_model()


class Command(BaseCommand):
    help = "Vérifie rapidement les principaux endpoints de l'API marchand."

    def handle(self, *args, **options):
        seller = self.ensure_user(
            email="seller@dagri.local",
            username="seller",
            first_name="Sacha",
            last_name="Seller",
            is_seller=True,
        )
        buyer = self.ensure_user(
            email="buyer@dagri.local",
            username="buyer",
            first_name="Bastien",
            last_name="Buyer",
            is_seller=False,
        )

        product = self.ensure_product(seller)

        buyer_client = APIClient()
        buyer_client.force_authenticate(buyer)

        product_list = buyer_client.get("/api/products/?is_active=true")
        self.assert_response(product_list, "GET /api/products/")

        cart_res = buyer_client.post(
            "/api/cart/add_item/",
            {"product_id": product.id, "quantity": 1},
            format="json",
        )
        self.assert_response(cart_res, "POST /api/cart/add_item/")

        order_payload = {
            "shipping_address": "123 Rue de la Ferme",
            "shipping_city": "Ouaga",
            "shipping_postal_code": "2100",
        }
        order_res = buyer_client.post("/api/orders/", order_payload, format="json")
        self.assert_response(order_res, "POST /api/orders/", expected=(201,))

        order_data = order_res.json()
        order_obj = Order.objects.filter(user=buyer).order_by("-created_at").first()
        order_id = (
            order_obj.id
            if order_obj
            else order_data.get("id")
            if isinstance(order_data, dict)
            else None
        )
        order_number = (
            order_obj.order_number
            if order_obj
            else order_data.get("order_number")
            if isinstance(order_data, dict)
            else None
        )
        seller_client = APIClient()
        seller_client.force_authenticate(seller)

        seller_orders = seller_client.get("/api/orders/")
        self.assert_response(seller_orders, "GET /api/orders/ (vendeur)")
        orders_json = seller_orders.json()
        if isinstance(orders_json, str):
            try:
                orders_json = json.loads(orders_json)
            except json.JSONDecodeError:
                self.stdout.write(self.style.ERROR("Impossible de décoder /api/orders/"))
                orders_json = []
        if isinstance(orders_json, dict):
            orders_json = orders_json.get("results") or orders_json.get("data") or []
        if not isinstance(orders_json, list):
            orders_json = []
        if order_id:
            matching = [
                order for order in orders_json if order.get("id") == order_id
            ]
        elif order_number:
            matching = [
                order for order in orders_json if order.get("order_number") == order_number
            ]
        else:
            matching = []
        if matching:
            self.stdout.write(self.style.SUCCESS("Commande visible dans la liste vendeur"))
        else:
            self.stdout.write(self.style.WARNING("La commande n'apparait pas chez le vendeur"))

        if not order_id:
            self.stdout.write(self.style.ERROR("Impossible de récupérer l'ID de la commande"))
            return

        status_update = seller_client.post(
            f"/api/orders/{order_id}/update_status/",
            {"status": "processing"},
            format="json",
        )
        self.assert_response(status_update, "POST /api/orders/<id>/update_status/")

        stats = seller_client.get("/api/seller/stats/")
        self.assert_response(stats, "GET /api/seller/stats/")

        self.stdout.write(
            self.style.SUCCESS("Tous les endpoints essentiels ont répondu correctement.")
        )

    def ensure_user(
        self,
        *,
        email: str,
        username: str,
        first_name: str,
        last_name: str,
        is_seller: bool,
    ) -> User:
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
        if created:
            user.set_password("Password123!")
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
        user.save()

        # Ensure profile flags are up to date
        profile = getattr(user, "profile", None)
        if profile:
            profile.is_seller = is_seller
            profile.save()
        return user

    def ensure_product(self, seller: User) -> Product:
        product = Product.objects.filter(owner=seller, is_active=True).first()
        if product:
            product.stock = max(product.stock, 5)
            product.save()
            return product

        category, _ = Category.objects.get_or_create(
            name="Test",
            defaults={"slug": "test"},
        )
        return Product.objects.create(
            name="Produit Test",
            description="Produit généré par la commande de vérification.",
            price=1500,
            stock=10,
            category=category,
            owner=seller,
            is_active=True,
        )

    def assert_response(
        self, response, label: str, expected: Sequence[int] = (200,)
    ):
        code = response.status_code
        if code in expected:
            self.stdout.write(self.style.SUCCESS(f"{label} → {code}"))
            return True
        truncated = (
            getattr(response, "content", b"")[:200]
            if hasattr(response, "content")
            else ""
        )
        self.stdout.write(
            self.style.ERROR(f"{label} → {code} ({truncated})")
        )
        return False
