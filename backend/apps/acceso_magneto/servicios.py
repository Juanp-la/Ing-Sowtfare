from django.conf import settings
from django.db.models import Count, Sum

from core.models import EjecucionAgente, HojaVida, Usuario
from core.servicios.archivos import guardar_archivo_hv
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


def importar_hv_magneto(usuario, cliente):
    """HU04: trae la HV del perfil de Magneto sin volver a cargarla.

    Devuelve (hoja_vida, creada). Si esa misma HV ya se importó (misma huella), devuelve la existente.
    Devuelve (None, False) si la cuenta no tiene HV en Magneto.
    """
    archivo = cliente.obtener_hv(usuario.magneto_id)
    if archivo is None:
        return None, False
    existente = HojaVida.objects.filter(usuario=usuario, origen=HojaVida.Origen.MAGNETO, huella=archivo.huella).first()
    if existente:
        return existente, False
    hv = HojaVida(usuario=usuario, nombre_archivo=archivo.nombre[:255], formato=archivo.formato,
                  origen=HojaVida.Origen.MAGNETO, huella=archivo.huella)
    guardar_archivo_hv(hv, archivo.contenido)
    hv.save()
    return hv, True
