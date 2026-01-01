"""
Kitchen Module Signal Handlers

Listens to sale_completed and other signals to create kitchen orders.
"""
import logging

from django.dispatch import receiver

from apps.core.signals import sale_created

logger = logging.getLogger(__name__)


@receiver(sale_created)
def on_sale_created(sender, sale, items, user, **kwargs):
    """
    When a sale is created, create a kitchen order if items need preparation.

    Args:
        sender: Signal sender
        sale: Sale object (or dict with sale info)
        items: List of sale items
        user: User who created the sale
    """
    from .models import KitchenConfig, KitchenOrder, KitchenOrderItem

    # Check if any items need kitchen preparation
    # (In a real implementation, products would have a 'requires_kitchen' flag)
    if not items:
        return

    config = KitchenConfig.get_config()

    # Get sale info
    sale_id = getattr(sale, 'id', str(sale.get('id', '')))
    table_id = getattr(sale, 'table_id', sale.get('table_id'))
    table_number = getattr(sale, 'table_number', sale.get('table_number', ''))
    order_number = getattr(sale, 'order_number', sale.get('order_number', sale_id[:8]))

    # Create kitchen order
    status = KitchenOrder.STATUS_PREPARING if config.auto_accept_orders else KitchenOrder.STATUS_PENDING

    kitchen_order = KitchenOrder.objects.create(
        sale_id=sale_id,
        table_id=table_id,
        table_number=table_number or '',
        order_number=order_number,
        status=status,
    )

    if config.auto_accept_orders:
        from django.utils import timezone
        kitchen_order.accepted_at = timezone.now()
        kitchen_order.save(update_fields=['accepted_at'])

    # Create order items
    for item in items:
        product_id = getattr(item, 'product_id', item.get('product_id', ''))
        product_name = getattr(item, 'product_name', item.get('product_name', 'Unknown'))
        quantity = getattr(item, 'quantity', item.get('quantity', 1))
        modifiers = getattr(item, 'modifiers', item.get('modifiers', ''))
        notes = getattr(item, 'notes', item.get('notes', ''))

        KitchenOrderItem.objects.create(
            order=kitchen_order,
            product_id=str(product_id),
            product_name=product_name,
            quantity=quantity,
            modifiers=modifiers,
            notes=notes,
        )

    logger.info(f"[KITCHEN] Created order #{kitchen_order.order_number} with {len(items)} items")
