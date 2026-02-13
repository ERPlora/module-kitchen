"""
Kitchen Display System (KDS) Models

The kitchen module provides the display/operational layer for kitchen staff.
Kitchen stations, orders, and station routing are defined in the orders module.
This module adds:
- KitchenSettings: Per-hub display and notification configuration
- KitchenOrderLog: Audit trail for order actions on the KDS
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import HubBaseModel


class KitchenSettings(HubBaseModel):
    """Per-hub settings for the Kitchen Display System."""

    # Display
    auto_accept_orders = models.BooleanField(default=False)
    show_timer = models.BooleanField(default=True)
    warning_time_minutes = models.PositiveIntegerField(default=15)
    critical_time_minutes = models.PositiveIntegerField(default=30)
    items_per_page = models.PositiveIntegerField(default=12)
    auto_refresh_seconds = models.PositiveIntegerField(default=10)

    # Sound
    sound_enabled = models.BooleanField(default=True)
    sound_on_new_order = models.BooleanField(default=True)
    sound_on_rush = models.BooleanField(default=True)

    # Auto-bump
    auto_bump_enabled = models.BooleanField(default=False)
    auto_bump_delay_seconds = models.PositiveIntegerField(default=5)

    # Color coding
    color_coding_enabled = models.BooleanField(default=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'kitchen_settings'
        verbose_name = _('Kitchen Settings')
        verbose_name_plural = _('Kitchen Settings')
        unique_together = [('hub_id',)]

    def __str__(self):
        return f"Kitchen Settings (Hub {self.hub_id})"

    @classmethod
    def get_settings(cls, hub_id):
        settings, _ = cls.all_objects.get_or_create(hub_id=hub_id)
        return settings


class KitchenOrderLog(HubBaseModel):
    """Audit trail for kitchen order actions."""

    ACTION_CHOICES = [
        ('received', _('Received')),
        ('accepted', _('Accepted')),
        ('started', _('Started')),
        ('bumped', _('Bumped')),
        ('completed', _('Completed')),
        ('served', _('Served')),
        ('recalled', _('Recalled')),
        ('cancelled', _('Cancelled')),
        ('priority_changed', _('Priority Changed')),
    ]

    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='kitchen_logs',
        verbose_name=_('Order'),
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='kitchen_logs',
        verbose_name=_('Order Item'),
    )
    station = models.ForeignKey(
        'orders.KitchenStation',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kitchen_logs',
        verbose_name=_('Station'),
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name=_('Action'))
    performed_by = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='kitchen_actions',
        verbose_name=_('Performed By'),
    )
    notes = models.TextField(blank=True)

    class Meta(HubBaseModel.Meta):
        db_table = 'kitchen_order_log'
        verbose_name = _('Kitchen Order Log')
        verbose_name_plural = _('Kitchen Order Logs')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.action} - Order #{self.order.order_number}"
