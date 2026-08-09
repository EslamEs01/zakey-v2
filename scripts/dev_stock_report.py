"""Report dev-database stock and order counts (E2E triage support)."""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from apps.inventory.models import StockItem  # noqa: E402
from apps.orders.models import Order  # noqa: E402

print(f"orders in dev DB: {Order.objects.count()}")
print("stock items:")
depleted = 0
for item in StockItem.objects.select_related("variant__product").order_by("variant__sku"):
    flag = ""
    if item.available <= 0:
        flag = "   <-- EXHAUSTED"
        depleted += 1
    print(f"  {item.variant.sku:24s} on_hand={item.on_hand:4d} "
          f"reserved={item.reserved:4d} available={item.available:4d}{flag}")
print(f"\nexhausted variants: {depleted} of {StockItem.objects.count()}")
