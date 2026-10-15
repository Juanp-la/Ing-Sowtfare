from django.conf import settings
from django.db.models import Count, Sum

from core.models import EjecucionAgente, Usuario
from core.servicios.cuota import ControlCuota


def vincular_usuario(perfil):
    """HU01: el candidato entra con su cuenta Magneto; no se crea un usuario aparte con otra clave."""
    usuario = (Usuario.objects.filter(magneto_id=perfil.magneto_id).first()
               or Usuario.objects.filter(email__iexact=perfil.email).first())
    if usuario is None:
        usuario = Usuario(
            email=perfil.email,
            username=f"magneto-{perfil.magneto_id}",
            cuota_tokens_mes=settings.CUOTA_TOKENS_DEFECTO,
        )
        usuario.set_unusable_password()  # la clave vive en Magneto, no en el copiloto
    usuario.magneto_id = perfil.magneto_id
    usuario.nombre = perfil.nombre
    usuario.save()
    return usuario


def consumo_por_agente(usuario):
    """NF04: tokens del mes por agente para el panel de consumo."""
    control = ControlCuota()
    return list(
        EjecucionAgente.objects.filter(usuario=usuario, fecha__gte=control.inicio_mes())
        .values("agente")
        .annotate(tokens=Sum("tokens"), ejecuciones=Count("id"))
        .order_by("-tokens", "agente")
    )
