"""Kitchen Display System URL Configuration"""

from django.urls import path
from . import views

app_name = 'kitchen'

urlpatterns = [
    # Display
    path('', views.index, name='index'),
    path('display/', views.display, name='display'),
    path('ready/', views.ready_orders, name='ready'),

    # Order actions
    path('orders/<uuid:order_id>/start/', views.start_order, name='start_order'),
    path('orders/<uuid:order_id>/bump/', views.bump_order, name='bump_order'),
    path('orders/<uuid:order_id>/complete/', views.complete_order, name='complete_order'),
    path('orders/<uuid:order_id>/serve/', views.serve_order, name='serve_order'),
    path('orders/<uuid:order_id>/recall/', views.recall_order, name='recall_order'),
    path('orders/<uuid:order_id>/priority/', views.set_priority, name='set_priority'),
    path('orders/<uuid:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),

    # Item actions
    path('items/<uuid:item_id>/bump/', views.bump_item, name='bump_item'),

    # Stations (read-only from orders module)
    path('stations/', views.stations, name='stations'),

    # History
    path('history/', views.history, name='history'),

    # API / Polling
    path('api/orders/', views.api_orders_list, name='api_orders_list'),
    path('api/count/', views.api_order_count, name='api_order_count'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/save/', views.settings_save, name='settings_save'),
    path('settings/toggle/', views.settings_toggle, name='settings_toggle'),
    path('settings/input/', views.settings_input, name='settings_input'),
    path('settings/reset/', views.settings_reset, name='settings_reset'),
]
