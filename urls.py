"""
Kitchen Module URLs
"""

from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    # Main views
    path('', views.display, name='display'),
    path('ready/', views.ready_orders, name='ready'),
    path('history/', views.history, name='history'),
    path('stations/', views.stations, name='stations'),

    # Order API
    path('api/accept/', views.api_accept_order, name='api_accept'),
    path('api/ready/', views.api_ready_order, name='api_ready'),
    path('api/serve/', views.api_serve_order, name='api_serve'),
    path('api/cancel/', views.api_cancel_order, name='api_cancel'),
    path('api/bump/', views.api_bump_order, name='api_bump'),

    # Item API
    path('api/item/ready/', views.api_item_ready, name='api_item_ready'),

    # Real-time updates
    path('api/orders/', views.api_orders_list, name='api_orders_list'),
    path('api/count/', views.api_order_count, name='api_order_count'),

    # Settings
    path('settings/', views.kitchen_settings, name='settings'),
    path('settings/save/', views.kitchen_settings_save, name='settings_save'),
    path('settings/toggle/', views.kitchen_settings_toggle, name='settings_toggle'),
    path('settings/input/', views.kitchen_settings_input, name='settings_input'),
    path('settings/reset/', views.kitchen_settings_reset, name='settings_reset'),
]
