"""
Patch para evitar conflito de format_suffix_patterns no Django REST Framework
"""

import rest_framework.urlpatterns as drf_urlpatterns
from django.urls.converters import register_converter

# Verificar se o converter já está registrado
def safe_register_converter(converter, type_name):
    try:
        register_converter(converter, type_name)
    except ValueError as e:
        if "is already registered" in str(e):
            pass  # Já está registrado, ignorar
        else:
            raise

# Aplicar patch
original_register_converter = drf_urlpatterns.register_converter
drf_urlpatterns.register_converter = safe_register_converter