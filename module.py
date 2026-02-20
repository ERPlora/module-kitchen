from django.utils.translation import gettext_lazy as _

MODULE_ID = 'kitchen'
MODULE_NAME = _('Kitchen Display')
MODULE_VERSION = '2.0.0'

MENU = {
    'label': _('Kitchen'),
    'icon': 'restaurant-outline',
    'order': 24,
}

NAVIGATION = [
    {'id': 'display', 'label': _('Display'), 'icon': 'tv-outline', 'view': ''},
    {'id': 'ready', 'label': _('Ready'), 'icon': 'checkmark-circle-outline', 'view': 'ready'},
    {'id': 'stations', 'label': _('Stations'), 'icon': 'flame-outline', 'view': 'stations'},
    {'id': 'history', 'label': _('History'), 'icon': 'time-outline', 'view': 'history'},
    {'id': 'settings', 'label': _('Settings'), 'icon': 'settings-outline', 'view': 'settings'},
]

PERMISSIONS = [
    'kitchen.view_kitchensettings',
    'kitchen.change_kitchensettings',
    'kitchen.view_kitchenorderlog',
]

DEPENDENCIES = ['orders']
