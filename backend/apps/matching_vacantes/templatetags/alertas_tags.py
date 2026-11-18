from django import template

from ..servicios import alertas_pendientes

register = template.Library()


@register.simple_tag
def alertas_sin_leer(usuario):
    """HU11: número de alertas sin leer para el indicador de la barra superior."""
    if not getattr(usuario, "is_authenticated", False) or getattr(usuario, "rol", "") == "reclutador":
        return 0
    return alertas_pendientes(usuario)
