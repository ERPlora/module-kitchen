"""AI tools for the Kitchen Display System (KDS) module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class GetKitchenDisplay(AssistantTool):
    name = "get_kitchen_display"
    description = "Get current kitchen display: active orders grouped by station with items, status, elapsed time, priority."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    parameters = {
        "type": "object",
        "properties": {
            "station_id": {"type": "string", "description": "Filter by station ID"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from orders.models import Order, OrderItem
        qs = Order.objects.filter(
            status__in=['pending', 'preparing'],
        ).select_related('table', 'waiter').order_by('created_at')
        orders_data = []
        for o in qs[:50]:
            items_qs = o.items.select_related('station').all()
            if args.get('station_id'):
                items_qs = items_qs.filter(station_id=args['station_id'])
            if not items_qs.exists() and args.get('station_id'):
                continue
            orders_data.append({
                "order_number": o.order_number,
                "status": o.status,
                "priority": o.priority,
                "order_type": o.order_type,
                "table": o.table.number if o.table else None,
                "elapsed_minutes": o.elapsed_minutes,
                "is_delayed": o.is_delayed,
                "items": [
                    {
                        "id": str(i.id),
                        "product_name": i.product_name,
                        "quantity": i.quantity,
                        "status": i.status,
                        "station": i.station.name if i.station else None,
                        "notes": i.notes,
                        "modifiers": i.modifiers,
                        "seat_number": i.seat_number,
                    }
                    for i in items_qs
                ],
            })
        return {"orders": orders_data, "total": len(orders_data)}


@register_tool
class ListReadyOrders(AssistantTool):
    name = "list_ready_orders"
    description = "List orders with status 'ready' awaiting service/pickup."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from orders.models import Order
        orders = Order.objects.filter(status='ready').select_related('table').order_by('ready_at')
        return {
            "orders": [
                {
                    "order_number": o.order_number,
                    "table": o.table.number if o.table else None,
                    "order_type": o.order_type,
                    "item_count": o.item_count,
                    "ready_at": o.ready_at.isoformat() if o.ready_at else None,
                }
                for o in orders[:50]
            ]
        }


@register_tool
class BumpOrderItem(AssistantTool):
    name = "bump_order_item"
    description = "Mark an order item as ready (bump). Auto-bumps the order if all items are done."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "item_id": {"type": "string", "description": "OrderItem ID to bump"},
        },
        "required": ["item_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from orders.models import OrderItem
        item = OrderItem.objects.select_related('order').get(id=args['item_id'])
        item.mark_ready()
        return {
            "item": item.product_name,
            "item_status": item.status,
            "order_number": item.order.order_number,
            "order_status": item.order.status,
            "bumped": True,
        }


@register_tool
class BumpOrder(AssistantTool):
    name = "bump_order"
    description = "Mark an entire order as ready."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order ID to bump"},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from orders.models import Order
        o = Order.objects.get(id=args['order_id'])
        o.mark_ready()
        return {"order_number": o.order_number, "status": o.status, "bumped": True}


@register_tool
class RecallOrder(AssistantTool):
    name = "recall_order"
    description = "Recall a bumped order back to preparing status."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Order ID to recall"},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from orders.models import Order
        o = Order.objects.get(id=args['order_id'])
        o.recall()
        return {"order_number": o.order_number, "status": o.status, "recalled": True}


@register_tool
class GetKitchenSettings(AssistantTool):
    name = "get_kitchen_settings"
    description = "Get kitchen display settings (timers, auto-bump, sounds, refresh rate)."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchensettings"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from kitchen.models import KitchenSettings
        s = KitchenSettings.get_settings()
        return {
            "auto_accept_orders": s.auto_accept_orders,
            "show_timer": s.show_timer,
            "warning_time_minutes": s.warning_time_minutes,
            "critical_time_minutes": s.critical_time_minutes,
            "items_per_page": s.items_per_page,
            "auto_refresh_seconds": s.auto_refresh_seconds,
            "sound_enabled": s.sound_enabled,
            "sound_on_new_order": s.sound_on_new_order,
            "sound_on_rush": s.sound_on_rush,
            "auto_bump_enabled": s.auto_bump_enabled,
            "auto_bump_delay_seconds": s.auto_bump_delay_seconds,
            "color_coding_enabled": s.color_coding_enabled,
        }


@register_tool
class UpdateKitchenSettings(AssistantTool):
    name = "update_kitchen_settings"
    description = "Update kitchen display settings."
    module_id = "kitchen"
    required_permission = "kitchen.change_kitchensettings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "auto_accept_orders": {"type": "boolean"},
            "show_timer": {"type": "boolean"},
            "warning_time_minutes": {"type": "integer"},
            "critical_time_minutes": {"type": "integer"},
            "items_per_page": {"type": "integer"},
            "auto_refresh_seconds": {"type": "integer"},
            "sound_enabled": {"type": "boolean"},
            "sound_on_new_order": {"type": "boolean"},
            "sound_on_rush": {"type": "boolean"},
            "auto_bump_enabled": {"type": "boolean"},
            "auto_bump_delay_seconds": {"type": "integer"},
            "color_coding_enabled": {"type": "boolean"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from kitchen.models import KitchenSettings
        s = KitchenSettings.get_settings()
        updated = []
        for field in ['auto_accept_orders', 'show_timer', 'warning_time_minutes',
                       'critical_time_minutes', 'items_per_page', 'auto_refresh_seconds',
                       'sound_enabled', 'sound_on_new_order', 'sound_on_rush',
                       'auto_bump_enabled', 'auto_bump_delay_seconds', 'color_coding_enabled']:
            if field in args:
                setattr(s, field, args[field])
                updated.append(field)
        if updated:
            s.save()
        return {"updated_fields": updated, "success": True}


@register_tool
class ListKitchenLogs(AssistantTool):
    name = "list_kitchen_logs"
    description = "List kitchen order logs (audit trail of order actions in the kitchen)."
    module_id = "kitchen"
    required_permission = "kitchen.view_kitchenorderlog"
    parameters = {
        "type": "object",
        "properties": {
            "order_id": {"type": "string", "description": "Filter by order ID"},
            "action": {"type": "string", "description": "Filter: received, accepted, started, bumped, completed, served, recalled, cancelled, priority_changed"},
            "station_id": {"type": "string", "description": "Filter by station ID"},
            "limit": {"type": "integer", "description": "Max results (default 50)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from kitchen.models import KitchenOrderLog
        qs = KitchenOrderLog.objects.select_related('order', 'station').all()
        if args.get('order_id'):
            qs = qs.filter(order_id=args['order_id'])
        if args.get('action'):
            qs = qs.filter(action=args['action'])
        if args.get('station_id'):
            qs = qs.filter(station_id=args['station_id'])
        limit = args.get('limit', 50)
        logs = qs.order_by('-created_at')[:limit]
        return {
            "logs": [
                {
                    "id": str(l.id),
                    "order_number": l.order.order_number if l.order else None,
                    "action": l.action,
                    "station": l.station.name if l.station else None,
                    "notes": l.notes,
                    "created_at": l.created_at.isoformat(),
                }
                for l in logs
            ]
        }
