"""
Tests for Kitchen module views.

Tests URL routing, authentication, and API endpoints.
"""

import pytest
import json

from django.urls import resolve

from kitchen import views
from kitchen.models import KitchenOrder, KitchenConfig


# ==============================================================================
# URL ROUTING TESTS
# ==============================================================================

@pytest.mark.django_db
class TestURLRouting:
    """Tests for URL routing and resolution."""

    def test_display_url_resolves(self):
        """Test display URL resolves."""
        resolver = resolve('/modules/kitchen/')
        assert resolver.func == views.display

    def test_ready_url_resolves(self):
        """Test ready orders URL resolves."""
        resolver = resolve('/modules/kitchen/ready/')
        assert resolver.func == views.ready_orders

    def test_history_url_resolves(self):
        """Test history URL resolves."""
        resolver = resolve('/modules/kitchen/history/')
        assert resolver.func == views.history

    def test_stations_url_resolves(self):
        """Test stations URL resolves."""
        resolver = resolve('/modules/kitchen/stations/')
        assert resolver.func == views.stations

    def test_api_accept_url_resolves(self):
        """Test API accept URL resolves."""
        resolver = resolve('/modules/kitchen/api/accept/')
        assert resolver.func == views.api_accept_order

    def test_api_ready_url_resolves(self):
        """Test API ready URL resolves."""
        resolver = resolve('/modules/kitchen/api/ready/')
        assert resolver.func == views.api_ready_order

    def test_api_serve_url_resolves(self):
        """Test API serve URL resolves."""
        resolver = resolve('/modules/kitchen/api/serve/')
        assert resolver.func == views.api_serve_order

    def test_api_cancel_url_resolves(self):
        """Test API cancel URL resolves."""
        resolver = resolve('/modules/kitchen/api/cancel/')
        assert resolver.func == views.api_cancel_order

    def test_api_bump_url_resolves(self):
        """Test API bump URL resolves."""
        resolver = resolve('/modules/kitchen/api/bump/')
        assert resolver.func == views.api_bump_order

    def test_api_item_ready_url_resolves(self):
        """Test API item ready URL resolves."""
        resolver = resolve('/modules/kitchen/api/item/ready/')
        assert resolver.func == views.api_item_ready

    def test_settings_url_resolves(self):
        """Test settings URL resolves."""
        resolver = resolve('/modules/kitchen/settings/')
        assert resolver.func == views.kitchen_settings


# ==============================================================================
# AUTHENTICATION TESTS
# ==============================================================================

@pytest.mark.django_db
class TestAuthentication:
    """Tests for view authentication requirements."""

    def test_display_requires_auth(self, client, store_config):
        """Test display requires authentication."""
        response = client.get('/modules/kitchen/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_ready_requires_auth(self, client, store_config):
        """Test ready orders requires authentication."""
        response = client.get('/modules/kitchen/ready/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_api_accept_requires_auth(self, client, store_config):
        """Test API accept requires authentication."""
        response = client.post('/modules/kitchen/api/accept/')
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_settings_requires_auth(self, client, store_config):
        """Test settings requires authentication."""
        response = client.get('/modules/kitchen/settings/')
        assert response.status_code == 302
        assert '/login/' in response.url


# ==============================================================================
# ORDER API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestOrderAPI:
    """Tests for order API endpoints."""

    def test_api_accept_order(self, auth_client, kitchen_order):
        """Test accepting an order."""
        response = auth_client.post(
            '/modules/kitchen/api/accept/',
            {'order_id': kitchen_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'preparing'

        kitchen_order.refresh_from_db()
        assert kitchen_order.status == KitchenOrder.STATUS_PREPARING

    def test_api_accept_non_pending_fails(self, auth_client, preparing_order):
        """Test accepting non-pending order fails."""
        response = auth_client.post(
            '/modules/kitchen/api/accept/',
            {'order_id': preparing_order.id}
        )
        assert response.status_code == 400
        data = json.loads(response.content)
        assert data['success'] is False

    def test_api_ready_order(self, auth_client, preparing_order):
        """Test marking order as ready."""
        response = auth_client.post(
            '/modules/kitchen/api/ready/',
            {'order_id': preparing_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'ready'

    def test_api_serve_order(self, auth_client, ready_order):
        """Test serving an order."""
        response = auth_client.post(
            '/modules/kitchen/api/serve/',
            {'order_id': ready_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'served'

    def test_api_serve_non_ready_fails(self, auth_client, preparing_order):
        """Test serving non-ready order fails."""
        response = auth_client.post(
            '/modules/kitchen/api/serve/',
            {'order_id': preparing_order.id}
        )
        assert response.status_code == 400

    def test_api_cancel_order(self, auth_client, kitchen_order):
        """Test cancelling an order."""
        response = auth_client.post(
            '/modules/kitchen/api/cancel/',
            {'order_id': kitchen_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'cancelled'

    def test_api_bump_pending_to_preparing(self, auth_client, kitchen_order):
        """Test bump pending order to preparing."""
        response = auth_client.post(
            '/modules/kitchen/api/bump/',
            {'order_id': kitchen_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'preparing'

    def test_api_bump_preparing_to_ready(self, auth_client, preparing_order):
        """Test bump preparing order to ready."""
        response = auth_client.post(
            '/modules/kitchen/api/bump/',
            {'order_id': preparing_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'ready'

    def test_api_bump_ready_to_served(self, auth_client, ready_order):
        """Test bump ready order to served."""
        response = auth_client.post(
            '/modules/kitchen/api/bump/',
            {'order_id': ready_order.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'served'


# ==============================================================================
# ITEM API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestItemAPI:
    """Tests for item API endpoints."""

    def test_api_item_ready(self, auth_client, kitchen_order_with_items):
        """Test marking item as ready."""
        item = kitchen_order_with_items.items.first()

        response = auth_client.post(
            '/modules/kitchen/api/item/ready/',
            {'item_id': item.id}
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True
        assert data['status'] == 'ready'


# ==============================================================================
# COUNT API TESTS
# ==============================================================================

@pytest.mark.django_db
class TestCountAPI:
    """Tests for order count API."""

    def test_api_order_count(self, auth_client, kitchen_order, preparing_order, ready_order):
        """Test order count API."""
        response = auth_client.get('/modules/kitchen/api/count/')
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['pending'] == 1
        assert data['preparing'] == 1
        assert data['ready'] == 1
        assert data['total'] == 2  # pending + preparing


# ==============================================================================
# SETTINGS TESTS
# ==============================================================================

@pytest.mark.django_db
class TestSettingsView:
    """Tests for settings views."""

    def test_settings_save_success(self, auth_client, store_config):
        """Test saving settings."""
        response = auth_client.post(
            '/modules/kitchen/settings/save/',
            json.dumps({
                'auto_accept_orders': True,
                'show_timer': False,
                'warning_time_minutes': 20,
                'critical_time_minutes': 40,
                'sound_enabled': False,
                'stations_enabled': True
            }),
            content_type='application/json'
        )
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['success'] is True

        config = KitchenConfig.get_config()
        assert config.auto_accept_orders is True
        assert config.show_timer is False
        assert config.warning_time_minutes == 20
        assert config.critical_time_minutes == 40
        assert config.sound_enabled is False
        assert config.stations_enabled is True

    def test_settings_save_invalid_json(self, auth_client, store_config):
        """Test saving settings with invalid JSON."""
        response = auth_client.post(
            '/modules/kitchen/settings/save/',
            'invalid json',
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_settings_toggle(self, auth_client, store_config):
        """Test toggling a boolean setting."""
        response = auth_client.post(
            '/modules/kitchen/settings/toggle/',
            {'name': 'auto_accept_orders', 'value': 'true'}
        )
        assert response.status_code == 204

        config = KitchenConfig.get_config()
        assert config.auto_accept_orders is True

    def test_settings_input(self, auth_client, store_config):
        """Test updating a numeric setting."""
        response = auth_client.post(
            '/modules/kitchen/settings/input/',
            {'name': 'warning_time_minutes', 'value': '25'}
        )
        assert response.status_code == 204

        config = KitchenConfig.get_config()
        assert config.warning_time_minutes == 25

    def test_settings_reset(self, auth_client, store_config):
        """Test resetting settings to defaults."""
        # First change some settings
        config = KitchenConfig.get_config()
        config.warning_time_minutes = 100
        config.auto_accept_orders = True
        config.save()

        # Reset
        response = auth_client.post('/modules/kitchen/settings/reset/')
        assert response.status_code == 204

        # Verify reset to defaults
        config.refresh_from_db()
        assert config.warning_time_minutes == 15
        assert config.auto_accept_orders is False
