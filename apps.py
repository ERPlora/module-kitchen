"""
Kitchen Module Django App Config
"""
from django.apps import AppConfig


class KitchenConfig(AppConfig):
    name = 'kitchen'
    verbose_name = 'Kitchen Display System'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Register signal handlers when app is ready."""
        from . import signals  # noqa: F401
