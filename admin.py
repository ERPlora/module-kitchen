"""
Kitchen Module Admin
"""

from django.contrib import admin
from .models import KitchenConfig, KitchenStation, KitchenOrder, KitchenOrderItem


@admin.register(KitchenConfig)
class KitchenConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'auto_accept_orders', 'warning_time_minutes', 'critical_time_minutes']


@admin.register(KitchenStation)
class KitchenStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['order', 'name']


class KitchenOrderItemInline(admin.TabularInline):
    model = KitchenOrderItem
    extra = 0
    readonly_fields = ['created_at']


@admin.register(KitchenOrder)
class KitchenOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'table_number', 'status', 'priority', 'elapsed_display', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'sale_id', 'table_number']
    readonly_fields = ['created_at', 'accepted_at', 'ready_at', 'served_at']
    inlines = [KitchenOrderItemInline]
    ordering = ['-created_at']


@admin.register(KitchenOrderItem)
class KitchenOrderItemAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'quantity', 'order', 'station', 'status']
    list_filter = ['status', 'station']
    search_fields = ['product_name', 'order__order_number']
