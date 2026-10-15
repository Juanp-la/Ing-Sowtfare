from django.db import transaction

from core.dominio.requisitos import evaluar_requisitos
from core.models import PerfilExtraido, PlanMejora, PreguntaEntrevista
from core.servicios.copiloto import CopilotoService


class ErrorPreparacion(Exception):
    """El agente Coach no pudo generar la preparación."""


def perfiles_del_usuario(usuario):
    return (PerfilExtraido.objects.filter(hoja_vida__usuario=usuario)
            .select_related("hoja_vida").order_by("-confirmado", "-hoja_vida__fecha_carga", "-id"))


def perfil_activo(usuario, hv_id=None):
    perfiles = perfiles_del_usuario(usuario)
    if hv_id and str(hv_id).isdigit():
        perfiles = perfiles.filter(hoja_vida_id=int(hv_id))
    return perfiles.first()


def brechas(perfil, vacante):
    return evaluar_requisitos(perfil.datos, vacante.requisitos)[1]


def _vacante_como_dict(vacante):
    return {"id": vacante.pk, "titulo": vacante.titulo, "empresa": vacante.empresa,
            "descripcion": vacante.descripcion, "requisitos": vacante.requisitos}


def preparar(usuario, perfil, vacante, servicio=None):
    """HU16 + HU17: ejecuta el Coach y guarda preguntas y plan (reemplaza la preparación anterior)."""
    hv = perfil.hoja_vida
    resultado = (servicio or CopilotoService()).ejecutar(
        usuario, "preparar", hoja_vida_id=hv.pk, vacante_id=vacante.pk,
        perfil=perfil.datos, vacante=_vacante_como_dict(vacante),
    )
    if resultado.get("error") or "preguntas" not in resultado:
        raise ErrorPreparacion(resultado.get("error", "sin resultado"))
    with transaction.atomic():
        PreguntaEntrevista.objects.filter(hoja_vida=hv, vacante=vacante).delete()
        for orden, p in enumerate(resultado["preguntas"], start=1):
            PreguntaEntrevista.objects.create(hoja_vida=hv, vacante=vacante, orden=orden, pregunta=p["pregunta"],
                                              tipo=p.get("tipo") or "tecnica", brecha=p.get("brecha", "")[:200],
                                              sugerencia=p.get("sugerencia", ""))
        plan = PlanMejora.objects.create(hoja_vida=hv, vacante=vacante, acciones=resultado["plan"],
                                         diagnostico=hv.diagnosticos.first())
    return plan


def preparacion_guardada(perfil, vacante):
    hv = perfil.hoja_vida
    return (PreguntaEntrevista.objects.filter(hoja_vida=hv, vacante=vacante),
            PlanMejora.objects.filter(hoja_vida=hv, vacante=vacante).first())
