"""
Kitchen Module Views

Provides views for:
- Kitchen display (orders list)
- Order management (accept, ready, serve)
- Settings
"""

import json

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.utils import timezone

from apps.modules_runtime.decorators import module_view

from .models import KitchenConfig, KitchenStation, KitchenOrder, KitchenOrderItem


# ==============================================================================
# MAIN VIEWS
# ==============================================================================

@login_required
@module_view("kitchen", "display")
def display(request):
    """Main kitchen display - shows pending and preparing orders."""
    orders = KitchenOrder.objects.filter(
        status__in=[KitchenOrder.STATUS_PENDING, KitchenOrder.STATUS_PREPARING]
    ).prefetch_related('items').order_by('-priority', 'created_at')

    config = KitchenConfig.get_config()

    return {
        'orders': orders,
        'config': config,
    }


@login_required
@module_view("kitchen", "ready")
def ready_orders(request):
    """Shows orders that are ready to be served."""
    orders = KitchenOrder.objects.filter(
        status=KitchenOrder.STATUS_READY
    ).prefetch_related('items').order_by('ready_at')

    return {
        'orders': orders,
    }


@login_required
@module_view("kitchen", "history")
def history(request):
    """Shows completed orders history."""
    orders = KitchenOrder.objects.filter(
        status__in=[KitchenOrder.STATUS_SERVED, KitchenOrder.STATUS_CANCELLED]
    ).prefetch_related('items').order_by('-served_at', '-created_at')[:50]

    return {
        'orders': orders,
    }


@login_required
@module_view("kitchen", "stations")
def stations(request):
    """Manage kitchen stations."""
    stations = KitchenStation.objects.all().order_by('order', 'name')

    return {
        'stations': stations,
    }


# ==============================================================================
# ORDER API
# ==============================================================================

@login_required
@require_POST
def api_accept_order(request):
    """Accept a pending order and start preparation."""
    order_id = request.POST.get('order_id')
    order = get_object_or_404(KitchenOrder, id=order_id)

    if order.status != KitchenOrder.STATUS_PENDING:
        return JsonResponse({
            'success': False,
            'error': _('Order is not pending')
        }, status=400)

    order.accept()

    return JsonResponse({
        'success': True,
        'status': order.status,
        'accepted_at': order.accepted_at.isoformat() if order.accepted_at else None,
    })


@login_required
@require_POST
def api_ready_order(request):
    """Mark an order as ready for service."""
    order_id = request.POST.get('order_id')
    order = get_object_or_404(KitchenOrder, id=order_id)

    if order.status not in [KitchenOrder.STATUS_PENDING, KitchenOrder.STATUS_PREPARING]:
        return JsonResponse({
            'success': False,
            'error': _('Order cannot be marked ready')
        }, status=400)

    order.mark_ready()

    return JsonResponse({
        'success': True,
        'status': order.status,
        'ready_at': order.ready_at.isoformat() if order.ready_at else None,
    })


@login_required
@require_POST
def api_serve_order(request):
    """Mark an order as served."""
    order_id = request.POST.get('order_id')
    order = get_object_or_404(KitchenOrder, id=order_id)

    if order.status != KitchenOrder.STATUS_READY:
        return JsonResponse({
            'success': False,
            'error': _('Order is not ready')
        }, status=400)

    order.mark_served()

    return JsonResponse({
        'success': True,
        'status': order.status,
        'served_at': order.served_at.isoformat() if order.served_at else None,
    })


@login_required
@require_POST
def api_cancel_order(request):
    """Cancel an order."""
    order_id = request.POST.get('order_id')
    order = get_object_or_404(KitchenOrder, id=order_id)

    if order.status in [KitchenOrder.STATUS_SERVED, KitchenOrder.STATUS_CANCELLED]:
        return JsonResponse({
            'success': False,
            'error': _('Order cannot be cancelled')
        }, status=400)

    order.cancel()

    return JsonResponse({
        'success': True,
        'status': order.status,
    })


@login_required
@require_POST
def api_bump_order(request):
    """Bump order to next status (quick action)."""
    order_id = request.POST.get('order_id')
    order = get_object_or_404(KitchenOrder, id=order_id)

    if order.status == KitchenOrder.STATUS_PENDING:
        order.accept()
    elif order.status == KitchenOrder.STATUS_PREPARING:
        order.mark_ready()
    elif order.status == KitchenOrder.STATUS_READY:
        order.mark_served()
    else:
        return JsonResponse({
            'success': False,
            'error': _('No action available')
        }, status=400)

    return JsonResponse({
        'success': True,
        'status': order.status,
    })


# ==============================================================================
# ITEM API
# ==============================================================================

@login_required
@require_POST
def api_item_ready(request):
    """Mark a single item as ready."""
    item_id = request.POST.get('item_id')
    item = get_object_or_404(KitchenOrderItem, id=item_id)

    item.mark_ready()

    return JsonResponse({
        'success': True,
        'status': item.status,
        'order_status': item.order.status,
    })


# ==============================================================================
# REAL-TIME UPDATES
# ==============================================================================

@login_required
def api_orders_list(request):
    """Return current orders as HTML partial (for polling/SSE)."""
    orders = KitchenOrder.objects.filter(
        status__in=[KitchenOrder.STATUS_PENDING, KitchenOrder.STATUS_PREPARING]
    ).prefetch_related('items').order_by('-priority', 'created_at')

    return render(request, 'kitchen/partials/orders_list.html', {
        'orders': orders,
    })


@login_required
def api_order_count(request):
    """Return pending order count."""
    pending = KitchenOrder.objects.filter(status=KitchenOrder.STATUS_PENDING).count()
    preparing = KitchenOrder.objects.filter(status=KitchenOrder.STATUS_PREPARING).count()
    ready = KitchenOrder.objects.filter(status=KitchenOrder.STATUS_READY).count()

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
@module_view("kitchen", "settings")
def kitchen_settings(request):
    """Settings view for the Kitchen module."""
    from django.urls import reverse
    config = KitchenConfig.get_config()

    return {
        'config': config,
        'kitchen_toggle_url': reverse('kitchen:settings_toggle'),
        'kitchen_input_url': reverse('kitchen:settings_input'),
    }


@require_http_methods(["POST"])
@login_required
def kitchen_settings_save(request):
    """Save kitchen settings via JSON."""
    try:
        data = json.loads(request.body)
        config = KitchenConfig.get_config()

        config.auto_accept_orders = data.get('auto_accept_orders', False)
        config.show_timer = data.get('show_timer', True)
        config.warning_time_minutes = data.get('warning_time_minutes', 15)
        config.critical_time_minutes = data.get('critical_time_minutes', 30)
        config.sound_enabled = data.get('sound_enabled', True)
        config.stations_enabled = data.get('stations_enabled', False)
        config.save()

        return JsonResponse({'success': True, 'message': 'Settings saved'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@require_http_methods(["POST"])
@login_required
def kitchen_settings_toggle(request):
    """Toggle a single setting via HTMX."""
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value', request.POST.get('setting_value', 'false'))
    setting_value = value == 'true' or value is True

    config = KitchenConfig.get_config()

    boolean_settings = ['auto_accept_orders', 'show_timer', 'sound_enabled', 'stations_enabled']

    if name in boolean_settings:
        setattr(config, name, setting_value)
        config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Setting updated')), 'color': 'success'}
    })
    return response


@require_http_methods(["POST"])
@login_required
def kitchen_settings_input(request):
    """Update a numeric setting via HTMX."""
    name = request.POST.get('name') or request.POST.get('setting_name')
    value = request.POST.get('value') or request.POST.get('setting_value')

    config = KitchenConfig.get_config()

    numeric_settings = ['warning_time_minutes', 'critical_time_minutes']

    if name in numeric_settings:
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


@require_http_methods(["POST"])
@login_required
def kitchen_settings_reset(request):
    """Reset all settings to defaults via HTMX."""
    config = KitchenConfig.get_config()

    config.auto_accept_orders = False
    config.show_timer = True
    config.warning_time_minutes = 15
    config.critical_time_minutes = 30
    config.sound_enabled = True
    config.stations_enabled = False
    config.save()

    response = HttpResponse(status=204)
    response['HX-Trigger'] = json.dumps({
        'showToast': {'message': str(_('Settings reset to defaults')), 'color': 'warning'},
        'refreshPage': True
    })
    return response
