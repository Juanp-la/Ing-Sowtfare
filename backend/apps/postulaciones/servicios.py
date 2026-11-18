from django.db import IntegrityError, transaction

from apps.acceso_magneto.clientes import ErrorMagneto, obtener_cliente_magneto
from core.models import HVAdaptada, PerfilExtraido, Postulacion
from core.servicios.copiloto import CopilotoService


class ErrorPostulacion(Exception):
    """No fue posible completar la postulación."""


class YaPostulado(ErrorPostulacion):
    """El candidato ya tiene una postulación para esa vacante."""


def opciones_hv(usuario, vacante):
    """HV que el candidato puede enviar: sus perfiles extraídos y las adaptaciones aplicadas a esa vacante."""
    perfiles = (PerfilExtraido.objects.filter(hoja_vida__usuario=usuario)
                .select_related("hoja_vida").order_by("-confirmado", "-hoja_vida__fecha_carga", "-id"))
    adaptadas = HVAdaptada.objects.filter(hoja_vida__usuario=usuario, vacante=vacante,
                                          estado=HVAdaptada.Estado.APLICADA).select_related("hoja_vida")
    return list(perfiles), list(adaptadas)


def postulacion_existente(usuario, vacante):
    return Postulacion.objects.filter(usuario=usuario, vacante=vacante).first()


def _vacante_como_dict(vacante):
    return {"id": vacante.pk, "titulo": vacante.titulo, "descripcion": vacante.descripcion,
            "requisitos": vacante.requisitos}


def calcular_ajuste(usuario, perfil_datos, vacante, hoja_vida_id=None, servicio=None):
    """Ajuste del perfil que se envía, calculado por el agente Matcher (intención buscar_vacantes)."""
    resultado = (servicio or CopilotoService()).ejecutar(
        usuario, "buscar_vacantes", hoja_vida_id=hoja_vida_id, perfil=perfil_datos,
        vacantes=[_vacante_como_dict(vacante)],
    )
    ajustes = resultado.get("ajustes") or []
    if resultado.get("error") or not ajustes:
        raise ErrorPostulacion(resultado.get("error", "sin ajuste"))
    return ajustes[0]


def postular(usuario, vacante, perfil=None, adaptacion=None, cliente=None, servicio=None):
    """HU15: envía la postulación a Magneto con la HV elegida (original o adaptada) y la registra."""
    if postulacion_existente(usuario, vacante):
        raise YaPostulado("Ya te postulaste a esta vacante.")
    if adaptacion is not None:
        datos, hoja_vida = adaptacion.perfil_adaptado, adaptacion.hoja_vida
    elif perfil is not None:
        datos, hoja_vida = perfil.datos, perfil.hoja_vida
    else:
        raise ErrorPostulacion("Elige la hoja de vida que quieres enviar.")
    ajuste = calcular_ajuste(usuario, datos, vacante, hoja_vida_id=hoja_vida.pk, servicio=servicio)
    try:
        magneto_id = (cliente or obtener_cliente_magneto()).postular(usuario.magneto_id, vacante.magneto_id, datos)
    except ErrorMagneto as exc:
        raise ErrorPostulacion(str(exc)) from exc
    try:
        with transaction.atomic():
            return Postulacion.objects.create(
                usuario=usuario, vacante=vacante, hoja_vida=hoja_vida, hv_adaptada=adaptacion,
                perfil_enviado=datos, score=ajuste["score"], cumple=ajuste["cumple"], no_cumple=ajuste["no_cumple"],
                magneto_id=magneto_id,
            )
    except IntegrityError as exc:  # doble clic: otra petición ya la creó
        raise YaPostulado("Ya te postulaste a esta vacante.") from exc


def retirar(postulacion):
    """HU18: el candidato retira una postulación que aún no ha sido decidida."""
    if not postulacion.abierta:
        raise ErrorPostulacion("La postulación ya fue decidida por el reclutador y no se puede retirar.")
    postulacion.delete()


def resumen_estados(usuario):
    conteo = {estado: 0 for estado, _ in Postulacion.Estado.choices}
    for estado in Postulacion.objects.filter(usuario=usuario).values_list("estado", flat=True):
        conteo[estado] += 1
    return [{"estado": e, "nombre": n, "total": conteo[e]} for e, n in Postulacion.Estado.choices]
