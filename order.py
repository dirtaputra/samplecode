"""Order service."""
from django.utils import dateformat, timezone
from django.db.models import F, FloatField, PositiveIntegerField, Sum

from bolu.models import Order, OrderCancelReason, OrderItem, Product
from bolu.services.common import common_service


class OrderService:
    """OrderService."""

    def batch_update_status(self, order_ids, status):
        """Update status of multiple orders."""
        cancel_status = Order.OrderStatus.DIBATALKAN.value

        orders = Order.objects.filter(id__in=order_ids)
        # update = orders.update(status=status)

        transaction_statuses = dict()

        for order in orders:
            current_status = order.status
            trx_status = True

            # if submit cancelation and current order status is not canceled
            if status == cancel_status and current_status != cancel_status:
                trx_status = self.revert_order_product_stock(order)

            # if submit status change from cancel to anything
            elif current_status == cancel_status:
                trx_status = self.aquire_order_product_stock(order)

            transaction_statuses[str(order.id)] = trx_status

            if trx_status:
                order = self.update_status_date(order, status)
                order.status = status
                order.save()

        return transaction_statuses

    def revert_order_product_stock(self, order):
        """Update product stock if order is canceled."""
        order_items = order.items.all()

        for item in order_items:
            product = item.product
            product.quantity = product.quantity + item.qty
            product.save()

        return True

    def aquire_order_product_stock(self, order):
        """Take stock from product to order item."""
        order_items = order.items.all()
        product_container = list()

        for item in order_items:
            # check if product quantity can be aquired by order items
            product = item.product

            if product.quantity < item.qty:
                return False

            product.quantity = product.quantity - item.qty
            product_container.append(product)

        for product in product_container:
            product.save()

        return True

    def update_status_date(self, order, status):
        """Update field status date."""
        now = timezone.now()

        if status == Order.OrderStatus.AKTIF.value:
            order.active_updated = now
        elif status == Order.OrderStatus.DIBAYAR.value:
            order.paid_updated = now
        elif status == Order.OrderStatus.DIKIRIM.value:
            order.sent_updated = now
        elif status == Order.OrderStatus.SELESAI.value:
            order.done_updated = now
        elif status == Order.OrderStatus.DIBATALKAN.value:
            order.canceled_updated = now

        return order

    def batch_remove(self, order_ids):
        """Remove multiple orders."""
        return Order.objects.filter(id__in=order_ids).delete(),

    def create_order_items(self, order, items):
        """Create order items."""
        for item in items:
            product_id = item['id']
            order_quantity = item['qty']
            product = Product.objects.get(pk=product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                qty=order_quantity,
                price=product.selling_price
            )
            product.quantity = product.quantity - order_quantity
            product.save()

    def update_order_items(self, order, items):
        """Update order items.

        Update order items, by posted order item
        if order item not in posted the remove
        if product posted not in order items then create
        """
        submited_products_dict = dict([(item['id'], item['qty']) for item in items])  # product id, qty
        submited_products_ids = submited_products_dict.keys()
        current_order_items = order.items.all()
        current_products_ids = []

        # search for current order items
        for item in current_order_items:
            product_id = item.product.id
            current_products_ids.append(product_id)

            if product_id in submited_products_ids:  # old order item
                order_qty = submited_products_dict[product_id]

                if order_qty != item.qty:  # change DB only if different in quantity
                    qty_diff = item.qty - order_qty
                    item.qty = order_qty
                    item.product.quantity = item.product.quantity + qty_diff  # reduce or increase product stock
                    item.product.save()
                    item.save()

            else:
                # order item to be removed
                # revert product stock
                item.product.quantity = item.product.quantity + item.qty
                item.product.save()
                item.delete()

        # search for new order items
        for product_id in submited_products_ids:

            if product_id not in current_products_ids:
                # add new product to order item
                order_qty = submited_products_dict[product_id]
                product = Product.objects.get(pk=product_id)
                product.quantity = product.quantity - order_qty  # reduce stock
                product.save()

                OrderItem.objects.create(  # new order item
                    order=order,
                    product=product,
                    price=product.selling_price,
                    qty=order_qty
                )

    def get_by_store(self, store):
        """Get order store."""
        return Order.objects.filter(store=store)

    def get_total_order(self, store, month):
        """Total Order."""
        if month is not None:
            return Order.objects.filter(store=store,
                                        created__month__gte=month,
                                        created__month__lte=month).count()

        return Order.objects.filter(store=store).count()

    def get_total_payment(self, store, month):
        """Total Payment."""
        index = 0
        total_payment = []
        # Filter_by_Month
        
        if month is not None:
            price = OrderItem.objects.filter(order__status=3,
                                             order__store=store,
                                             order__done_updated__month__gte=month,
                                             order__done_updated__month__lte=month).\
                                             values('order').\
                                             annotate(total_payment=Sum(F('qty') * F('product__price'), output_field=FloatField()))
            selling_price = OrderItem.objects.filter(order__status=3,
                                                    order__store=store,
                                                    order__done_updated__month__gte=month,
                                                    order__done_updated__month__lte=month).\
                                                    values('order').\
                                                    annotate(total_payment=Sum(F('qty') * F('price'), output_field=FloatField()))
            for i in selling_price:
                total_payment.append(i['total_payment'] - price[index]['total_payment'])
                index += 1
                
            if total_payment is None:
                total_payment = 0
            else:
                total_payment = sum(total_payment)
                                        
            return total_payment
        # Filter_AllTime
        price = OrderItem.objects.filter(order__store=store,
                                        order__status=3).values('order').\
                                        annotate(total_payment=Sum(F('qty') * F('product__price'), output_field=FloatField()))
        selling_price = OrderItem.objects.filter(order__store=store,
                                                order__status=3).values('order').\
                                                annotate(total_payment=Sum(F('qty') * F('price'), output_field=FloatField()))

        for i in selling_price:
            total_payment.append(i['total_payment'] - price[index]['total_payment'])
            index += 1

        if total_payment is None:
            total_payment = 0
        else:
            total_payment= sum(total_payment)

        return total_payment

    def create_order_number(self, store):
        """Create new order number based on last order number per store perday."""
        order = Order.objects.filter(store=store, created__date=timezone.now().date()).order_by('-order_number').first()
        order_number = 1

        if order and order.order_number > 0:
            order_number = order.order_number + 1

        return order_number

    def create_invoice_number(self, store, order_number=None, order_type='NB'):
        """Create invoice number per store.

        order type:
            BR: Brand
            NB: Non Brand

        TT-UIDYYMMDD-0001
        TT (Type/Tag): BR/NB --> Brand or Non-brand
        UID (User ID): From Bolu app
        YYMMDD: (example --> 200803)
        Numerical Order: 4 digits, up to 9999
        """
        uid = store.id.hex[:4]
        today = timezone.now()
        dt = dateformat.format(today, 'ymd')

        if not order_number:
            order_number = self.create_order_number(store)

        if order_number < 1000:
            order_number = str(10000 + order_number)[-4:]

        return f'{order_type}-{uid}{dt}-{order_number}'

    def batch_create_cancelation_reason(self, order_ids, option_id, description):
        """Create multiple cancelation reasons."""
        for order_id in order_ids:
            OrderCancelReason.objects.create(
                order_id=order_id,
                order_cancel_option_id=option_id,
                description=description
            )

    def get_by_id(self, order_id):
        """Get by id."""
        order = Order.objects.filter(id=order_id).first()
        return order

    def get_item_by_order(self, order_id):
        """Get OrderItem by order."""
        item = OrderItem.objects.filter(order=order_id)
        return item

    def get_dropship_customer(self, order_id):
        """Get dropshipper."""
        dropshipper = Order.objects.filter(id=order_id).values_list('dropship_customer', flat=True).first()
        return dropshipper

    def get_total_weight(self, order_id):
        """Get total weight."""
        total_weight = OrderItem.objects.filter(order=order_id).\
                  aggregate(total_weigth=Sum(F('qty') * F('product__weight'),flat=True, 
                  output_field=PositiveIntegerField())).get('total_weigth')
        
        if total_weight >= 1000:
            total_kg = total_weight / 1000
            return f"{total_kg} kg"
        
        return f"{total_weight} gr"
    
    def get_courier_price(self, order_id):
        """Get courier price."""
        price = Order.objects.filter(id=order_id).values_list('courier_price', flat=True).first()
        rupiah = common_service.format_rupiah(price)

        return rupiah


order_service = OrderService()
