"""
Pytest configuration for Kitchen module tests.
"""

import os
import sys
from pathlib import Path

# Ensure Django settings are configured before any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Add the hub directory to Python path
HUB_DIR = Path(__file__).resolve().parent.parent.parent.parent / 'hub'
if str(HUB_DIR) not in sys.path:
    sys.path.insert(0, str(HUB_DIR))

# Add the modules directory to Python path
MODULES_DIR = Path(__file__).resolve().parent.parent.parent
if str(MODULES_DIR) not in sys.path:
    sys.path.insert(0, str(MODULES_DIR))

# Now setup Django
import django
django.setup()

# Disable debug toolbar during tests to avoid namespace errors
from django.conf import settings
if 'debug_toolbar' in settings.INSTALLED_APPS:
    settings.INSTALLED_APPS = [
        app for app in settings.INSTALLED_APPS if app != 'debug_toolbar'
    ]
if hasattr(settings, 'MIDDLEWARE'):
    settings.MIDDLEWARE = [
        m for m in settings.MIDDLEWARE if 'debug_toolbar' not in m
    ]

# Import pytest and fixtures
import pytest
from django.test import Client
from django.utils import timezone

from apps.accounts.models import LocalUser
from apps.configuration.models import StoreConfig


@pytest.fixture
def client():
    """Create test client."""
    return Client()


@pytest.fixture
def local_user(db):
    """Create a test local user."""
    from django.contrib.auth.hashers import make_password
    return LocalUser.objects.create(
        name='Test User',
        email='test@example.com',
        role='admin',
        pin_hash=make_password('1234'),
        is_active=True
    )


@pytest.fixture
def store_config(db):
    """Create store configuration (marks hub as configured)."""
    config = StoreConfig.get_config()
    config.is_configured = True
    config.name = 'Test Store'
    config.save()
    return config


@pytest.fixture
def auth_client(client, local_user, store_config):
    """Create authenticated test client with session."""
    session = client.session
    session['local_user_id'] = str(local_user.id)
    session['user_name'] = local_user.name
    session['user_email'] = local_user.email
    session['user_role'] = local_user.role
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def kitchen_config(db):
    """Create kitchen config."""
    from kitchen.models import KitchenConfig
    return KitchenConfig.get_config()


@pytest.fixture
def station(db):
    """Create a test kitchen station."""
    from kitchen.models import KitchenStation
    return KitchenStation.objects.create(
        name="Grill Station",
        code="GRILL",
        color="#ff6b6b",
        order=1,
        is_active=True
    )


@pytest.fixture
def kitchen_order(db):
    """Create a test kitchen order."""
    from kitchen.models import KitchenOrder
    return KitchenOrder.objects.create(
        sale_id="sale-123",
        order_number="001",
        table_number="5",
        status=KitchenOrder.STATUS_PENDING,
    )


@pytest.fixture
def kitchen_order_with_items(db, kitchen_order, station):
    """Create kitchen order with items."""
    from kitchen.models import KitchenOrderItem

    KitchenOrderItem.objects.create(
        order=kitchen_order,
        product_id="prod-1",
        product_name="Burger",
        quantity=2,
        station=station,
    )
    KitchenOrderItem.objects.create(
        order=kitchen_order,
        product_id="prod-2",
        product_name="Fries",
        quantity=1,
        station=station,
    )
    return kitchen_order


@pytest.fixture
def preparing_order(db):
    """Create an order in preparing status."""
    from kitchen.models import KitchenOrder
    order = KitchenOrder.objects.create(
        sale_id="sale-456",
        order_number="002",
        status=KitchenOrder.STATUS_PREPARING,
    )
    order.accepted_at = timezone.now()
    order.save()
    return order


@pytest.fixture
def ready_order(db):
    """Create an order in ready status."""
    from kitchen.models import KitchenOrder
    order = KitchenOrder.objects.create(
        sale_id="sale-789",
        order_number="003",
        status=KitchenOrder.STATUS_READY,
    )
    order.accepted_at = timezone.now()
    order.ready_at = timezone.now()
    order.save()
    return order
