import os
import django
import sys

# Add the current directory to sys.path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment - using 'settings' directly as it's in the same dir
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from market.models import Category, Product
from django.contrib.auth import get_user_model

User = get_user_model()

def populate():
    print("Starting database population...")

    # 1. Create Categories
    categories_data = [
        "Fruits", "Légumes", "Céréales", "Produits laitiers", 
        "Viandes", "Volailles", "Œufs", "Miel et produits de la ruche", 
        "Plantes aromatiques", "Huiles et condiments"
    ]

    cats = {}
    for name in categories_data:
        cat, created = Category.objects.get_or_create(
            name=name, 
            defaults={'slug': name.lower().replace(' ', '-')}
        )
        cats[name] = cat
        if created:
            print(f"Created category: {name}")

    # 2. Get or Create a Seller User
    user, created = User.objects.get_or_create(
        username="vendeur_test", 
        defaults={'email': "vendeur@test.com"}
    )
    if created:
        user.set_password("password123")
        user.is_seller = True
        user.save()
        print("Created test seller: vendeur_test")
    elif not user.is_seller:
        user.is_seller = True
        user.save()
        print("Updated existing user to seller")

    # 3. Create Sample Products
    products_data = [
        {
            "name": "Tomates Fraîches",
            "description": "Tomates rouges et juteuses, idéales pour salades et sauces.",
            "price": 1200,
            "unit": "kg",
            "category": "Légumes",
            "stock": 50
        },
        {
            "name": "Pommes de terre",
            "description": "Pommes de terre locales, chair ferme.",
            "price": 5000,
            "unit": "bag",
            "category": "Légumes",
            "stock": 20
        },
        {
            "name": "Miel Pur",
            "description": "Miel de fleurs sauvages, 100% naturel.",
            "price": 3500,
            "unit": "liter",
            "category": "Miel et produits de la ruche",
            "stock": 15
        },
        {
            "name": "Œufs de ferme",
            "description": "Plateau de 30 œufs frais.",
            "price": 2500,
            "unit": "piece",
            "category": "Œufs",
            "stock": 100
        },
        {
            "name": "Riz Local (Parfumé)",
            "description": "Sac de 50kg de riz local parfumé de haute qualité.",
            "price": 22000,
            "unit": "bag",
            "category": "Céréales",
            "stock": 10
        }
    ]

    for p_data in products_data:
        cat_name = p_data.pop("category")
        # Check if product already exists to avoid duplicates
        if not Product.objects.filter(name=p_data['name'], owner=user).exists():
            Product.objects.create(
                owner=user,
                category=cats.get(cat_name, cats["Légumes"]), # Fallback
                is_active=True,
                **p_data
            )
            print(f"Created product: {p_data['name']}")
        else:
            print(f"Product already exists: {p_data['name']}")

    print("Database population complete!")

if __name__ == "__main__":
    populate()
