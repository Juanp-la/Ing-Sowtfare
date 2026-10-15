import time
import uuid

from django.db import transaction
from django.utils import timezone

from core.models import Diagnostico, EjecucionAgente, Hallazgo, HojaVida, PerfilExtraido, Usuario
from core.servicios import tareas
from core.servicios.copiloto import CopilotoService
from core.servicios.cuota import ControlCuota, CuotaAgotada

MENSAJE_ILEGIBLE = "No fue posible leer el archivo, intente con otro formato"
UMBRAL_SEGUNDOS = 30  # NF01


class SinPerfil(Exception):
    """La HV aún no tiene perfil extraído: primero hay que analizarla."""


def _perfil(hv):
    return PerfilExtraido.objects.filter(hoja_vida=hv).first()


def iniciar_diagnostico(usuario, hv):
    """HU05 / NF01: crea el diagnóstico y lo ejecuta en segundo plano sin bloquear la interfaz."""
    perfil = _perfil(hv)
    if hv.estado == HojaVida.Estado.ERROR or (perfil is not None and not perfil.datos):
        return Diagnostico.objects.create(hoja_vida=hv, estado=Diagnostico.Estado.ERROR, mensaje_error=MENSAJE_ILEGIBLE)
    if perfil is None:
        raise SinPerfil()
    if not ControlCuota().verificar(usuario):
        raise CuotaAgotada("Alcanzaste tu cuota mensual de uso del copiloto.")
    diagnostico = Diagnostico.objects.create(hoja_vida=hv, ejecucion_id=uuid.uuid4().hex)
    transaction.on_commit(lambda: tareas.lanzar(ejecutar_diagnostico, diagnostico.pk))
    return diagnostico


def ejecutar_diagnostico(diagnostico_id, servicio=None):
    """Corre el grafo (intención "diagnosticar") y guarda puntaje, hallazgos y explicación."""
    diagnostico = Diagnostico.objects.select_related("hoja_vida").get(pk=diagnostico_id)
    hv = diagnostico.hoja_vida
    usuario = Usuario.objects.get(pk=hv.usuario_id)
    inicio = time.perf_counter()
    try:
        resultado = (servicio or CopilotoService()).ejecutar(
            usuario, "diagnosticar", hoja_vida_id=hv.pk, ejecucion_id=diagnostico.ejecucion_id,
            perfil=_perfil(hv).datos, texto_hv=hv.texto_extraido,
        )
    except CuotaAgotada:
        resultado = {"error": "cuota_agotada"}
    diagnostico.duracion_ms = int((time.perf_counter() - inicio) * 1000)

    if resultado.get("error") or resultado.get("puntaje") is None:
        diagnostico.estado = Diagnostico.Estado.ERROR
        diagnostico.mensaje_error = ("Alcanzaste tu cuota mensual de uso del copiloto."
                                     if resultado.get("error") == "cuota_agotada"
                                     else "El diagnóstico no pudo completarse. Intenta de nuevo.")
        diagnostico.save()
        return diagnostico

    with transaction.atomic():
        diagnostico.puntaje = resultado["puntaje"]
        diagnostico.nivel = resultado["nivel"]
        diagnostico.criterios = resultado["criterios"]
        diagnostico.explicacion = resultado.get("explicacion", "")
        diagnostico.estado = Diagnostico.Estado.COMPLETADO
        diagnostico.save()
        for hallazgo in resultado.get("hallazgos", []):
            Hallazgo.objects.create(diagnostico=diagnostico, **hallazgo)
    return diagnostico


def tiempos_por_nodo(diagnostico):
    """NF01: duración de cada nodo de esta ejecución (desde EjecucionAgente)."""
    if not diagnostico.ejecucion_id:
        return []
    return list(EjecucionAgente.objects.filter(ejecucion_id=diagnostico.ejecucion_id)
                .order_by("id").values("agente", "duracion_ms", "tokens", "estado"))


def estado_diagnostico(diagnostico):
    segundos = (timezone.now() - diagnostico.fecha).total_seconds()
    return {
        "estado": diagnostico.estado,
        "terminado": diagnostico.estado != Diagnostico.Estado.PROCESANDO,
        "segundos": round(segundos, 1),
        "lento": diagnostico.estado == Diagnostico.Estado.PROCESANDO and segundos > UMBRAL_SEGUNDOS,
        "nodos": [n["agente"] for n in tiempos_por_nodo(diagnostico)],
        "puntaje": diagnostico.puntaje,
    }
