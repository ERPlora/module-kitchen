"""
Kitchen Module Models

Provides models for:
- KitchenConfig: Module settings (singleton)
- KitchenStation: Kitchen preparation stations (grill, salads, etc.)
- KitchenOrder: Orders sent to kitchen
- KitchenOrderItem: Individual items within an order
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class KitchenConfig(models.Model):
    """
    Singleton configuration for kitchen display settings.
    """
    auto_accept_orders = models.BooleanField(
        default=False,
        help_text=_("Automatically accept incoming orders")
    )
    show_timer = models.BooleanField(
        default=True,
        help_text=_("Show elapsed time on orders")
    )
    warning_time_minutes = models.PositiveIntegerField(
        default=15,
        help_text=_("Minutes until order shows warning color")
    )
    critical_time_minutes = models.PositiveIntegerField(
        default=30,
        help_text=_("Minutes until order shows critical color")
    )
    sound_enabled = models.BooleanField(
        default=True,
        help_text=_("Play sound on new orders")
    )
    stations_enabled = models.BooleanField(
        default=False,
        help_text=_("Enable kitchen stations")
    )

    class Meta:
        verbose_name = _("Kitchen Configuration")
        verbose_name_plural = _("Kitchen Configuration")

    def __str__(self):
        return "Kitchen Configuration"

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class KitchenStation(models.Model):
    """
    Kitchen preparation station (e.g., grill, salads, desserts).
    Items can be routed to specific stations.
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    color = models.CharField(
        max_length=7,
        default="#3880ff",
        help_text=_("Hex color for station display")
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = _("Kitchen Station")
        verbose_name_plural = _("Kitchen Stations")

    def __str__(self):
        return self.name


class KitchenOrder(models.Model):
    """
    An order sent to the kitchen for preparation.
    Links to a sale from the sales module.
    """
    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'
    STATUS_SERVED = 'served'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PREPARING, _('Preparing')),
        (STATUS_READY, _('Ready')),
        (STATUS_SERVED, _('Served')),
        (STATUS_CANCELLED, _('Cancelled')),
    ]

    # Reference to sale (string ID to avoid hard dependency)
    sale_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text=_("Reference to the sale in sales module")
    )

    # Optional table reference
    table_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Reference to table if from tables module")
    )
    table_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text=_("Table number for display")
    )

    # Order info
    order_number = models.CharField(
        max_length=50,
        db_index=True,
        help_text=_("Display order number")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True
    )
    priority = models.PositiveIntegerField(
        default=0,
        help_text=_("Higher number = higher priority")
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text=_("Special instructions for kitchen")
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    served_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', 'created_at']
        verbose_name = _("Kitchen Order")
        verbose_name_plural = _("Kitchen Orders")
        indexes = [
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Order #{self.order_number}"

    @property
    def elapsed_minutes(self):
        """Calculate elapsed time since order was created."""
        delta = timezone.now() - self.created_at
        return int(delta.total_seconds() / 60)

    @property
    def elapsed_display(self):
        """Return elapsed time as HH:MM string."""
        minutes = self.elapsed_minutes
        hours = minutes // 60
        mins = minutes % 60
        if hours > 0:
            return f"{hours}:{mins:02d}"
        return f"{mins}m"

    @property
    def status_class(self):
        """Return CSS class based on elapsed time."""
        if self.status in [self.STATUS_READY, self.STATUS_SERVED, self.STATUS_CANCELLED]:
            return ''

        config = KitchenConfig.get_config()
        minutes = self.elapsed_minutes

        if minutes >= config.critical_time_minutes:
            return 'critical'
        elif minutes >= config.warning_time_minutes:
            return 'warning'
        return ''

    def accept(self):
        """Mark order as being prepared."""
        self.status = self.STATUS_PREPARING
        self.accepted_at = timezone.now()
        self.save(update_fields=['status', 'accepted_at'])

    def mark_ready(self):
        """Mark order as ready for service."""
        self.status = self.STATUS_READY
        self.ready_at = timezone.now()
        self.save(update_fields=['status', 'ready_at'])

    def mark_served(self):
        """Mark order as served."""
        self.status = self.STATUS_SERVED
        self.served_at = timezone.now()
        self.save(update_fields=['status', 'served_at'])

    def cancel(self):
        """Cancel the order."""
        self.status = self.STATUS_CANCELLED
        self.save(update_fields=['status'])


class KitchenOrderItem(models.Model):
    """
    Individual item within a kitchen order.
    """
    STATUS_PENDING = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_READY = 'ready'

    STATUS_CHOICES = [
        (STATUS_PENDING, _('Pending')),
        (STATUS_PREPARING, _('Preparing')),
        (STATUS_READY, _('Ready')),
    ]

    order = models.ForeignKey(
        KitchenOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    station = models.ForeignKey(
        KitchenStation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )

    # Product info (copied from sale to avoid dependency)
    product_id = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)

    # Item-level notes/modifiers
    modifiers = models.TextField(
        blank=True,
        default='',
        help_text=_("Modifiers like 'no onions', 'extra cheese'")
    )
    notes = models.TextField(
        blank=True,
        default='',
        help_text=_("Special instructions for this item")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = _("Kitchen Order Item")
        verbose_name_plural = _("Kitchen Order Items")

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

    def mark_preparing(self):
        """Mark item as being prepared."""
        self.status = self.STATUS_PREPARING
        self.save(update_fields=['status'])

    def mark_ready(self):
        """Mark item as ready."""
        self.status = self.STATUS_READY
        self.save(update_fields=['status'])
        # Check if all items are ready
        self._check_order_ready()

    def _check_order_ready(self):
        """Check if all items in order are ready."""
        pending = self.order.items.exclude(status=self.STATUS_READY).exists()
        if not pending:
            self.order.mark_ready()
