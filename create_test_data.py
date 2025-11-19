"""
Script pour créer des données de test pour D-AGRI MARKET
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.contrib.auth import get_user_model
from market.models import Category, Product
from accounts.models import UserProfile

User = get_user_model()

def create_test_data():
    print("🌱 Création des données de test...")
    
    # 1. Créer des catégories
    print("\n📁 Création des catégories...")
    categories_data = [
        "Légumes",
        "Fruits",
        "Produits laitiers",
        "Œufs & Volaille",
        "Produits apicoles",
        "Céréales & Légumineuses",
    ]
    
    categories = {}
    for cat_name in categories_data:
        cat, created = Category.objects.get_or_create(name=cat_name)
        categories[cat_name] = cat
        if created:
            print(f"  ✅ Créé: {cat_name}")
        else:
            print(f"  ℹ️  Existe déjà: {cat_name}")
    
    # 2. Créer un utilisateur vendeur de test
    print("\n👤 Création d'un utilisateur vendeur...")
    seller, created = User.objects.get_or_create(
        username="fermier_dupont",
        defaults={
            "email": "fermier@example.com",
            "first_name": "Jean",
            "last_name": "Dupont"
        }
    )
    
    if created:
        seller.set_password("password123")
        seller.save()
        print(f"  ✅ Créé: {seller.username}")
    else:
        print(f"  ℹ️  Existe déjà: {seller.username}")
    
    # 3. Configurer le profil vendeur
    print("\n🏪 Configuration du profil vendeur...")
    profile = seller.profile
    profile.is_seller = True
    profile.business_name = "Ferme du Soleil"
    profile.business_description = "Producteur local de fruits et légumes biologiques depuis 1985"
    profile.business_address = "123 Chemin des Champs"
    profile.business_city = "Campagne-sur-Mer"
    profile.business_postal_code = "75001"
    profile.phone = "01 23 45 67 89"
    profile.save()
    print(f"  ✅ Profil vendeur configuré pour {seller.username}")
    
    # 4. Créer des produits
    print("\n🥬 Création des produits...")
    products_data = [
        {
            "name": "Tomates biologiques",
            "description": "Tomates cultivées sans pesticides, récoltées à maturité. Variété ancienne au goût authentique.",
            "price": 4.50,
            "stock": 50,
            "category": categories["Légumes"],
        },
        {
            "name": "Carottes fraîches",
            "description": "Carottes croquantes et sucrées, cultivées en pleine terre. Idéales pour vos salades et jus.",
            "price": 3.20,
            "stock": 75,
            "category": categories["Légumes"],
        },
        {
            "name": "Laitue biologique",
            "description": "Laitue fraîche du jour, cultivée sans produits chimiques. Parfaite pour vos salades.",
            "price": 2.80,
            "stock": 40,
            "category": categories["Légumes"],
        },
        {
            "name": "Pommes de saison",
            "description": "Pommes croquantes et juteuses, variétés locales. Parfaites pour croquer ou cuisiner.",
            "price": 5.99,
            "stock": 100,
            "category": categories["Fruits"],
        },
        {
            "name": "Fromage fermier",
            "description": "Fromage artisanal au lait cru, affiné 3 mois. Goût authentique et texture crémeuse.",
            "price": 12.00,
            "stock": 25,
            "category": categories["Produits laitiers"],
        },
        {
            "name": "Œufs fermiers",
            "description": "Œufs de poules élevées en plein air, nourries aux grains bio. Boîte de 6.",
            "price": 6.50,
            "stock": 60,
            "category": categories["Œufs & Volaille"],
        },
        {
            "name": "Miel naturel",
            "description": "Miel de fleurs sauvages, récolté artisanalement. Pot de 500g.",
            "price": 8.50,
            "stock": 30,
            "category": categories["Produits apicoles"],
        },
        {
            "name": "Yaourt maison",
            "description": "Yaourt nature au lait entier, sans additifs. Lot de 4 pots.",
            "price": 4.20,
            "stock": 45,
            "category": categories["Produits laitiers"],
        },
        {
            "name": "Courgettes bio",
            "description": "Courgettes tendres et savoureuses, cultivées sans pesticides.",
            "price": 3.80,
            "stock": 55,
            "category": categories["Légumes"],
        },
        {
            "name": "Fraises de saison",
            "description": "Fraises parfumées et sucrées, cueillies le matin même. Barquette de 500g.",
            "price": 7.50,
            "stock": 35,
            "category": categories["Fruits"],
        },
    ]
    
    for product_data in products_data:
        product, created = Product.objects.get_or_create(
            name=product_data["name"],
            owner=seller,
            defaults={
                "description": product_data["description"],
                "price": product_data["price"],
                "stock": product_data["stock"],
                "category": product_data["category"],
                "is_active": True,
            }
        )
        
        if created:
            print(f"  ✅ Créé: {product.name} - {product.price}€")
        else:
            print(f"  ℹ️  Existe déjà: {product.name}")
    
    print("\n✨ Données de test créées avec succès!")
    print(f"\n📊 Résumé:")
    print(f"  - Catégories: {Category.objects.count()}")
    print(f"  - Produits: {Product.objects.count()}")
    print(f"  - Vendeurs: {UserProfile.objects.filter(is_seller=True).count()}")
    
    print(f"\n🔐 Identifiants de test:")
    print(f"  Admin:")
    print(f"    - Username: admin")
    print(f"    - Password: (à définir via: uv run manage.py changepassword admin)")
    print(f"  Vendeur:")
    print(f"    - Username: fermier_dupont")
    print(f"    - Password: password123")

if __name__ == "__main__":
    create_test_data()
