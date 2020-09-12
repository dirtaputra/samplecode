"""Product service."""
from django.db.models import Sum

from bolu.models import Order, Product


class ProductService:
    """Product service."""
    def get_total_product(self, store):
        """Total Product."""
        return Product.objects.filter(store=store, is_deleted=False).count()

    def get_total_product_sold(self, store, month):
        """Total Product."""
        if month is not None:
            return Order.objects.filter(store=store,
                                        status=3,
                                        done_updated__month__gte=month,
                                        done_updated__month__lte=month).aggregate(Sum('items__qty')).get('items__qty__sum')

        return Order.objects.filter(store=store, status=3).aggregate(Sum('items__qty')).get('items__qty__sum')


product_service = ProductService()
