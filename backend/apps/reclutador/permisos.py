from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

ROLES_RECLUTADOR = ("reclutador", "admin")


def es_reclutador(usuario):
    return usuario.is_authenticated and (usuario.rol in ROLES_RECLUTADOR or usuario.is_superuser)


def reclutador_requerido(vista):
    """Solo reclutadores (o administradores) entran al módulo; un candidato recibe 403."""

    @login_required
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not es_reclutador(request.user):
            raise PermissionDenied("Módulo exclusivo para reclutadores.")
        return vista(request, *args, **kwargs)

    return envoltura
