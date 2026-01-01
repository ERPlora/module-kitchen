"""
Unit tests for Kitchen module models.
"""

import pytest
from datetime import timedelta
from django.utils import timezone

from kitchen.models import KitchenConfig, KitchenStation, KitchenOrder, KitchenOrderItem


# ==============================================================================
# KITCHEN CONFIG TESTS
# ==============================================================================

@pytest.mark.django_db
class TestKitchenConfig:
    """Tests for KitchenConfig model."""

    def test_get_config_creates_singleton(self):
        """Test get_config creates config if not exists."""
        config = KitchenConfig.get_config()
        assert config is not None
        assert config.pk == 1

    def test_config_default_values(self):
        """Test default configuration values."""
        config = KitchenConfig.get_config()
        assert config.auto_accept_orders is False
        assert config.show_timer is True
        assert config.warning_time_minutes == 15
        assert config.critical_time_minutes == 30
        assert config.sound_enabled is True
        assert config.stations_enabled is False

    def test_config_str(self):
        """Test config string representation."""
        config = KitchenConfig.get_config()
        assert str(config) == "Kitchen Configuration"

    def test_config_is_singleton(self):
        """Test only one config exists."""
        config1 = KitchenConfig.get_config()
        config1.warning_time_minutes = 20
        config1.save()

        config2 = KitchenConfig.get_config()
        assert config1.pk == config2.pk
        assert config2.warning_time_minutes == 20


# ==============================================================================
# KITCHEN STATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestKitchenStation:
    """Tests for KitchenStation model."""

    def test_station_creation(self, station):
        """Test station is created correctly."""
        assert station.name == "Grill Station"
        assert station.code == "GRILL"
        assert station.is_active is True

    def test_station_str(self, station):
        """Test station string representation."""
        assert str(station) == "Grill Station"

    def test_station_ordering(self, db):
        """Test stations are ordered by order field."""
        station1 = KitchenStation.objects.create(name="Last", code="LAST", order=10)
        station2 = KitchenStation.objects.create(name="First", code="FIRST", order=1)
        station3 = KitchenStation.objects.create(name="Middle", code="MID", order=5)

        stations = list(KitchenStation.objects.all())
        assert stations[0].code == "FIRST"
        assert stations[1].code == "MID"
        assert stations[2].code == "LAST"

    def test_station_unique_code(self, station, db):
        """Test station code must be unique."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            KitchenStation.objects.create(name="Duplicate", code="GRILL")


# ==============================================================================
# KITCHEN ORDER TESTS
# ==============================================================================

@pytest.mark.django_db
class TestKitchenOrder:
    """Tests for KitchenOrder model."""

    def test_order_creation(self, kitchen_order):
        """Test order is created correctly."""
        assert kitchen_order.sale_id == "sale-123"
        assert kitchen_order.order_number == "001"
        assert kitchen_order.status == KitchenOrder.STATUS_PENDING
        assert kitchen_order.table_number == "5"

    def test_order_str(self, kitchen_order):
        """Test order string representation."""
        assert str(kitchen_order) == "Order #001"

    def test_elapsed_minutes(self, db):
        """Test elapsed time calculation."""
        order = KitchenOrder.objects.create(
            sale_id="test",
            order_number="100",
        )
        # Override created_at
        order.created_at = timezone.now() - timedelta(minutes=25)
        order.save()

        assert order.elapsed_minutes >= 24  # Allow for test timing

    def test_elapsed_display_minutes(self, db):
        """Test elapsed display for minutes only."""
        order = KitchenOrder.objects.create(
            sale_id="test",
            order_number="100",
        )
        order.created_at = timezone.now() - timedelta(minutes=25)
        order.save()

        display = order.elapsed_display
        assert "m" in display or ":" in display

    def test_elapsed_display_hours(self, db):
        """Test elapsed display for hours:minutes."""
        order = KitchenOrder.objects.create(
            sale_id="test",
            order_number="100",
        )
        order.created_at = timezone.now() - timedelta(hours=1, minutes=30)
        order.save()

        display = order.elapsed_display
        assert ":" in display

    def test_status_class_normal(self, kitchen_order):
        """Test status class for new orders."""
        assert kitchen_order.status_class == ''

    def test_status_class_warning(self, db):
        """Test status class for warning time."""
        config = KitchenConfig.get_config()
        config.warning_time_minutes = 10
        config.critical_time_minutes = 20
        config.save()

        order = KitchenOrder.objects.create(sale_id="test", order_number="100")
        order.created_at = timezone.now() - timedelta(minutes=15)
        order.save()

        assert order.status_class == 'warning'

    def test_status_class_critical(self, db):
        """Test status class for critical time."""
        config = KitchenConfig.get_config()
        config.warning_time_minutes = 10
        config.critical_time_minutes = 20
        config.save()

        order = KitchenOrder.objects.create(sale_id="test", order_number="100")
        order.created_at = timezone.now() - timedelta(minutes=25)
        order.save()

        assert order.status_class == 'critical'

    def test_accept_order(self, kitchen_order):
        """Test accepting an order."""
        kitchen_order.accept()
        assert kitchen_order.status == KitchenOrder.STATUS_PREPARING
        assert kitchen_order.accepted_at is not None

    def test_mark_ready(self, preparing_order):
        """Test marking order as ready."""
        preparing_order.mark_ready()
        assert preparing_order.status == KitchenOrder.STATUS_READY
        assert preparing_order.ready_at is not None

    def test_mark_served(self, ready_order):
        """Test marking order as served."""
        ready_order.mark_served()
        assert ready_order.status == KitchenOrder.STATUS_SERVED
        assert ready_order.served_at is not None

    def test_cancel_order(self, kitchen_order):
        """Test cancelling an order."""
        kitchen_order.cancel()
        assert kitchen_order.status == KitchenOrder.STATUS_CANCELLED

    def test_order_priority_ordering(self, db):
        """Test orders are sorted by priority."""
        low = KitchenOrder.objects.create(
            sale_id="low", order_number="001", priority=0
        )
        high = KitchenOrder.objects.create(
            sale_id="high", order_number="002", priority=10
        )
        medium = KitchenOrder.objects.create(
            sale_id="med", order_number="003", priority=5
        )

        orders = list(KitchenOrder.objects.all())
        assert orders[0].sale_id == "high"
        assert orders[1].sale_id == "med"
        assert orders[2].sale_id == "low"


# ==============================================================================
# KITCHEN ORDER ITEM TESTS
# ==============================================================================

@pytest.mark.django_db
class TestKitchenOrderItem:
    """Tests for KitchenOrderItem model."""

    def test_item_creation(self, kitchen_order_with_items):
        """Test items are created correctly."""
        items = kitchen_order_with_items.items.all()
        assert items.count() == 2

        burger = items.filter(product_name="Burger").first()
        assert burger.quantity == 2

    def test_item_str(self, kitchen_order_with_items):
        """Test item string representation."""
        burger = kitchen_order_with_items.items.filter(product_name="Burger").first()
        assert str(burger) == "2x Burger"

    def test_mark_item_preparing(self, kitchen_order_with_items):
        """Test marking item as preparing."""
        item = kitchen_order_with_items.items.first()
        item.mark_preparing()
        assert item.status == KitchenOrderItem.STATUS_PREPARING

    def test_mark_item_ready(self, kitchen_order_with_items):
        """Test marking item as ready."""
        item = kitchen_order_with_items.items.first()
        item.mark_ready()
        assert item.status == KitchenOrderItem.STATUS_READY

    def test_all_items_ready_marks_order_ready(self, kitchen_order_with_items):
        """Test order is marked ready when all items are ready."""
        kitchen_order_with_items.accept()

        for item in kitchen_order_with_items.items.all():
            item.mark_ready()

        kitchen_order_with_items.refresh_from_db()
        assert kitchen_order_with_items.status == KitchenOrder.STATUS_READY

    def test_some_items_ready_order_still_preparing(self, kitchen_order_with_items):
        """Test order stays preparing when only some items are ready."""
        kitchen_order_with_items.accept()

        # Only mark first item ready
        first_item = kitchen_order_with_items.items.first()
        first_item.mark_ready()

        kitchen_order_with_items.refresh_from_db()
        assert kitchen_order_with_items.status == KitchenOrder.STATUS_PREPARING

    def test_item_with_modifiers(self, kitchen_order, station):
        """Test item with modifiers."""
        item = KitchenOrderItem.objects.create(
            order=kitchen_order,
            product_id="prod-3",
            product_name="Salad",
            quantity=1,
            modifiers="No onions, Extra cheese",
            notes="Allergic to nuts",
            station=station,
        )

        assert item.modifiers == "No onions, Extra cheese"
        assert item.notes == "Allergic to nuts"

    def test_item_station_relationship(self, kitchen_order_with_items, station):
        """Test item station relationship."""
        item = kitchen_order_with_items.items.first()
        assert item.station == station
        assert station.items.count() == 2
