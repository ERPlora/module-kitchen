from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class KitchenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'kitchen'
    label = 'kitchen'
    verbose_name = _('Kitchen Display System')

    def ready(self):
        pass
