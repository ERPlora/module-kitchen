"""
Kitchen Module Configuration

This file defines the module metadata and navigation for the Kitchen module.
Kitchen Display System (KDS) for managing orders and tickets in restaurant kitchens.
Used by the @module_view decorator to automatically render navigation tabs.
"""
from django.utils.translation import gettext_lazy as _

# Module Identification
MODULE_ID = "kitchen"
MODULE_NAME = _("Kitchen Display")
MODULE_ICON = "restaurant-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "horeca"  # Changed from "restaurant" to valid category

# Target Industries (business verticals this module is designed for)
MODULE_INDUSTRIES = [
    "restaurant", # Restaurants
    "fast_food",  # Fast food
    "catering",   # Catering & events
    "hotel",      # Hotels & lodging
]

# Sidebar Menu Configuration
MENU = {
    "label": _("Kitchen"),
    "icon": "restaurant-outline",
    "order": 50,
    "show": True,
}

# Internal Navigation (Tabs)
NAVIGATION = [
    {
        "id": "dashboard",
        "label": _("Display"),
        "icon": "tv-outline",
        "view": "",
    },
    {
        "id": "orders",
        "label": _("Orders"),
        "icon": "receipt-outline",
        "view": "orders",
    },
    {
        "id": "stations",
        "label": _("Stations"),
        "icon": "flame-outline",
        "view": "stations",
    },
    {
        "id": "settings",
        "label": _("Settings"),
        "icon": "settings-outline",
        "view": "settings",
    },
]

# Module Dependencies
DEPENDENCIES = ["orders>=1.0.0"]

# Default Settings
SETTINGS = {
    "auto_bump_enabled": False,
    "auto_bump_delay_seconds": 300,
    "sound_notifications": True,
    "color_coding_enabled": True,
}

# Permissions
PERMISSIONS = [
    "kitchen.view_display",
    "kitchen.bump_orders",
    "kitchen.manage_stations",
    "kitchen.configure_settings",
]
