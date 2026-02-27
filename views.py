"""Kitchen Display System Views

KDS display layer — consumes orders from orders.models.
Stations are managed in the orders module; kitchen is read-only for stations.
"""

import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.utils.translation import gettext as _
from django.utils import timezone
from django.db.models import Q

from apps.accounts.decorators import login_required, permission_required
from apps.core.htmx import htmx_view

from orders.models import Order, OrderItem, KitchenStation
from .models import KitchenSettings, KitchenOrderLog


# ── helpers ──────────────────────────────────────────────────────────────────

def _hub(request):
    return request.session.get('hub_id')


def _employee(request):
    from apps.accounts.models import LocalUser
    uid = request.session.get('local_user_id')
    if uid:
        return LocalUser.objects.filter(pk=uid).first()
    return None


def _log(hub_id, order, action, performed_by, item=None, station=None, notes=''):
    KitchenOrderLog.objects.create(
        hub_id=hub_id,
        order=order,
        item=item,
        station=station,
        action=action,
        performed_by=performed_by,
        notes=notes,
    )


# ==============================================================================
# INDEX
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/index.html', 'kitchen/partials/index.html')
def index(request):
    return display(request)


# ==============================================================================
# DISPLAY
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/display.html', 'kitchen/partials/display.html')
def display(request):
    """Main KDS — pending + preparing orders."""
    hub = _hub(request)
    settings = KitchenSettings.get_settings(hub)
    station_id = request.GET.get('station')

    orders = Order.objects.filter(
        hub_id=hub,
        is_deleted=False,
        status__in=['pending', 'preparing'],
    ).select_related('table', 'waiter').prefetch_related('items').order_by('-priority', 'created_at')

    if station_id:
        orders = orders.filter(items__station_id=station_id).distinct()

    stations = KitchenStation.objects.filter(hub_id=hub, is_deleted=False, is_active=True).order_by('sort_order')

    return {
        'orders': orders,
        'stations': stations,
        'settings': settings,
        'selected_station': station_id,
    }


# ==============================================================================
# READY ORDERS
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/ready.html', 'kitchen/partials/ready.html')
def ready_orders(request):
    """Orders that are ready to be served."""
    hub = _hub(request)
    orders = Order.objects.filter(
        hub_id=hub, is_deleted=False, status='ready',
    ).select_related('table', 'waiter').prefetch_related('items').order_by('ready_at')

    return {'orders': orders}


# ==============================================================================
# ORDER ACTIONS
# ==============================================================================

@login_required
@require_POST
def start_order(request, order_id):
    """Accept/start preparing an order."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)

    if order.status != 'pending':
        return JsonResponse({'success': False, 'error': _('Order is not pending')}, status=400)

    order.fire()
    _log(hub, order, 'started', _employee(request))
    return JsonResponse({'success': True, 'status': order.status})


@login_required
@require_POST
def bump_order(request, order_id):
    """Bump order to next status (quick action)."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)
    emp = _employee(request)

    if order.status == 'pending':
        order.fire()
        _log(hub, order, 'started', emp)
    elif order.status == 'preparing':
        order.mark_ready()
        _log(hub, order, 'completed', emp)
    elif order.status == 'ready':
        order.mark_served()
        _log(hub, order, 'served', emp)
    else:
        return JsonResponse({'success': False, 'error': _('No action available')}, status=400)

    return JsonResponse({'success': True, 'status': order.status})


@login_required
@require_POST
def complete_order(request, order_id):
    """Mark order as ready."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)

    if order.status not in ('pending', 'preparing'):
        return JsonResponse({'success': False, 'error': _('Order cannot be marked ready')}, status=400)

    order.mark_ready()
    _log(hub, order, 'completed', _employee(request))
    return JsonResponse({'success': True, 'status': order.status})


@login_required
@require_POST
def serve_order(request, order_id):
    """Mark order as served."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)

    if order.status != 'ready':
        return JsonResponse({'success': False, 'error': _('Order is not ready')}, status=400)

    order.mark_served()
    _log(hub, order, 'served', _employee(request))
    return JsonResponse({'success': True, 'status': order.status})


@login_required
@require_POST
def recall_order(request, order_id):
    """Recall a served order back to ready."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)

    if order.status != 'served':
        return JsonResponse({'success': False, 'error': _('Order cannot be recalled')}, status=400)

    order.recall()
    _log(hub, order, 'recalled', _employee(request))
    return JsonResponse({'success': True, 'status': order.status})


@login_required
@require_POST
def set_priority(request, order_id):
    """Set order priority (normal, rush, vip)."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)
    priority = request.POST.get('priority', 'normal')

    if priority not in ('normal', 'rush', 'vip'):
        return JsonResponse({'success': False, 'error': _('Invalid priority')}, status=400)

    old_priority = order.priority
    order.priority = priority
    order.save(update_fields=['priority', 'updated_at'])
    _log(hub, order, 'priority_changed', _employee(request), notes=f'{old_priority} → {priority}')
    return JsonResponse({'success': True, 'priority': order.priority})


@login_required
@require_POST
def cancel_order(request, order_id):
    """Cancel an order."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)

    if order.status in ('served', 'paid', 'cancelled'):
        return JsonResponse({'success': False, 'error': _('Order cannot be cancelled')}, status=400)

    reason = request.POST.get('reason', '')
    order.cancel(reason)
    _log(hub, order, 'cancelled', _employee(request), notes=reason)
    return JsonResponse({'success': True, 'status': order.status})


# ==============================================================================
# ORDER DETAIL
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/order_detail.html', 'kitchen/partials/order_detail.html')
def order_detail(request, order_id):
    """View order detail with kitchen log."""
    hub = _hub(request)
    order = get_object_or_404(Order, pk=order_id, hub_id=hub, is_deleted=False)
    items = order.items.filter(is_deleted=False).select_related('station', 'product').order_by('created_at')
    logs = KitchenOrderLog.objects.filter(
        hub_id=hub, order=order, is_deleted=False,
    ).select_related('performed_by', 'item', 'station').order_by('-created_at')[:50]

    return {'order': order, 'items': items, 'logs': logs}


# ==============================================================================
# ITEM ACTIONS
# ==============================================================================

@login_required
@require_POST
def bump_item(request, item_id):
    """Bump a single item to ready."""
    hub = _hub(request)
    item = get_object_or_404(OrderItem, pk=item_id, order__hub_id=hub, is_deleted=False)

    item.mark_ready()
    _log(hub, item.order, 'item_bumped', _employee(request), item=item, station=item.station,
         notes=item.product_name)
    return JsonResponse({
        'success': True,
        'item_status': item.status,
        'order_status': item.order.status,
    })


# ==============================================================================
# STATIONS (read-only from orders module)
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/stations.html', 'kitchen/partials/stations.html')
def stations(request):
    """View kitchen stations (managed in orders module)."""
    hub = _hub(request)
    station_list = KitchenStation.objects.filter(
        hub_id=hub, is_deleted=False,
    ).order_by('sort_order', 'name')

    # Count pending items per station
    for st in station_list:
        st.pending = OrderItem.objects.filter(
            order__hub_id=hub, station=st, is_deleted=False,
            status__in=['pending', 'preparing'],
        ).count()

    return {'stations': station_list}


# ==============================================================================
# HISTORY
# ==============================================================================

@login_required
@htmx_view('kitchen/pages/history.html', 'kitchen/partials/history.html')
def history(request):
    """Completed/cancelled orders history."""
    hub = _hub(request)
    search = request.GET.get('q', '').strip()
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    orders = Order.objects.filter(
        hub_id=hub, is_deleted=False,
        status__in=['served', 'paid', 'cancelled'],
    ).select_related('table', 'waiter').order_by('-updated_at')

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(notes__icontains=search)
        )
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    orders = orders[:100]

    return {
        'orders': orders,
        'search': search,
        'date_from': date_from or '',
        'date_to': date_to or '',
    }


# ==============================================================================
# API / POLLING
# ==============================================================================

@login_required
def api_orders_list(request):
    """Return pending+preparing orders as JSON for polling."""
    hub = _hub(request)
    station_id = request.GET.get('station')

    orders = Order.objects.filter(
        hub_id=hub, is_deleted=False,
        status__in=['pending', 'preparing'],
    ).select_related('table', 'waiter').prefetch_related('items').order_by('-priority', 'created_at')

    if station_id:
        orders = orders.filter(items__station_id=station_id).distinct()

    data = []
    for o in orders:
        items = []
        for it in o.items.filter(is_deleted=False):
            items.append({
                'id': str(it.pk),
                'product_name': it.product_name,
                'quantity': it.quantity,
                'modifiers': it.modifiers,
                'notes': it.notes,
                'status': it.status,
                'station_id': str(it.station_id) if it.station_id else None,
            })
        data.append({
            'id': str(o.pk),
            'order_number': o.order_number,
            'status': o.status,
            'priority': o.priority,
            'order_type': o.order_type,
            'table': o.table_display,
            'waiter': str(o.waiter) if o.waiter else '',
            'elapsed_minutes': o.elapsed_minutes,
            'item_count': o.item_count,
            'notes': o.notes,
            'items': items,
            'created_at': o.created_at.isoformat(),
        })

    return JsonResponse({'orders': data})


@login_required
def api_order_count(request):
    """Return order counts by status."""
    hub = _hub(request)
    pending = Order.objects.filter(hub_id=hub, is_deleted=False, status='pending').count()
    preparing = Order.objects.filter(hub_id=hub, is_deleted=False, status='preparing').count()
    ready = Order.objects.filter(hub_id=hub, is_deleted=False, status='ready').count()

    return JsonResponse({
        'pending': pending,
        'preparing': preparing,
        'ready': ready,
        'total': pending + preparing,
    })


# ==============================================================================
# SETTINGS
# ==============================================================================

@login_required
@permission_required('kitchen.manage_settings')
@htmx_view('kitchen/pages/settings.html', 'kitchen/partials/settings.html')
def settings(request):
    """Kitchen display settings."""
    hub = _hub(request)
    config = KitchenSettings.get_settings(hub)
    return {'config': config}


@login_required
@permission_required('kitchen.manage_settings')
@require_POST
def settings_save(request):
    """Save kitchen settings via JSON."""
    hub = _hub(request)
    try:
        data = json.loads(request.body)
        config = KitchenSettings.get_settings(hub)

        for field in [
            'auto_accept_orders', 'show_timer', 'sound_enabled',
            'sound_on_new_order', 'sound_on_rush', 'auto_bump_enabled',
            'color_coding_enabled',
        ]:
            if field in data:
                setattr(config, field, bool(data[field]))

        for field in [
            'warning_time_minutes', 'critical_time_minutes',
            'items_per_page', 'auto_refresh_seconds', 'auto_bump_delay',
        ]:
            if field in data:
                try:
                    setattr(config, field, int(data[field]))
                except (ValueError, TypeError):
                    pass

        config.save()
        return JsonResponse({'success': True, 'message': _('Settings saved')})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': _('Invalid JSON')}, status=400)


@login_required
@permission_required('kitchen.manage_settings')
@require_POST
def settings_toggle(request):
    """Toggle a single boolean setting via HTMX."""
    hub = _hub(request)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value', request.POST.get('setting_value', 'false'))
    setting_value = value == 'true' or value is True

    config = KitchenSettings.get_settings(hub)

    boolean_fields = [
        'auto_accept_orders', 'show_timer', 'sound_enabled',
        'sound_on_new_order', 'sound_on_rush', 'auto_bump_enabled',
        'color_coding_enabled',
    ]
    if name in boolean_fields:
        setattr(config, name, setting_value)
        config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@login_required
@require_POST
def settings_input(request):
    """Update a numeric setting via HTMX."""
    hub = _hub(request)
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value') or request.POST.get('setting_value')

    config = KitchenSettings.get_settings(hub)

    numeric_fields = [
        'warning_time_minutes', 'critical_time_minutes',
        'items_per_page', 'auto_refresh_seconds', 'auto_bump_delay',
    ]
    if name in numeric_fields:
        try:
            setattr(config, name, int(value))
            config.save()
        except (ValueError, TypeError):
            pass

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@login_required
@require_POST
def settings_reset(request):
    """Reset all settings to defaults."""
    hub = _hub(request)
    config = KitchenSettings.get_settings(hub)

    config.auto_accept_orders = False
    config.show_timer = True
    config.warning_time_minutes = 15
    config.critical_time_minutes = 30
    config.items_per_page = 20
    config.auto_refresh_seconds = 10
    config.sound_enabled = True
    config.sound_on_new_order = 'bell'
    config.sound_on_rush = 'alert'
    config.auto_bump_enabled = False
    config.auto_bump_delay = 5
    config.color_coding_enabled = True
    config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Settings reset to defaults')), 'color': 'warning'},
        'refreshPage': True,
    })
    return response
