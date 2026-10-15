from django import template

from core.servicios.cuota import ControlCuota

register = template.Library()


@register.simple_tag
def resumen_cuota(usuario):
    if not getattr(usuario, "is_authenticated", False):
        return None
    return ControlCuota().resumen(usuario)
