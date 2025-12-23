import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app_agri.settings')
django.setup()

from market.models import Product

try:
    products = Product.objects.filter(is_active=True)
    count = products.count()
    print(f"Active products count: {count}")
    for p in products[:5]:
        print(f"- {p.name} (Stock: {p.stock}, Price: {p.price})")
except Exception as e:
    print(f"Error: {e}")
