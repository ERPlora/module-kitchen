"""
Kitchen Module Configuration
"""

MODULE_ID = 'kitchen'
MODULE_VERSION = '1.0.0'


def get_module_info():
    """Return module metadata."""
    return {
        'module_id': MODULE_ID,
        'name': 'Kitchen Display System',
        'name_es': 'Sistema de Pantalla de Cocina',
        'version': MODULE_VERSION,
        'description': 'Kitchen display system for managing orders and tickets',
        'description_es': 'Sistema de pantalla de cocina para gestionar pedidos y comandas',
        'author': 'ERPlora',
        'category': 'restaurant',
    }
