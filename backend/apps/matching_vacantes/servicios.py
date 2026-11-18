from django.conf import settings
from django.db import transaction
from django.db.models import Max, Min
from django.utils import timezone

from core.models import AjusteVacante, AlertaVacante, PerfilExtraido, Usuario, Vacante
from core.servicios.copiloto import CopilotoService
from core.servicios.cuota import CuotaAgotada

UMBRAL_ALERTA_DEFECTO = 70


def perfiles_del_usuario(usuario):
    return (PerfilExtraido.objects.filter(hoja_vida__usuario=usuario)
            .select_related("hoja_vida").order_by("-confirmado", "-hoja_vida__fecha_carga", "-id"))


def perfil_activo(usuario, hv_id=None):
    perfiles = perfiles_del_usuario(usuario)
    if hv_id and str(hv_id).isdigit():
        perfiles = perfiles.filter(hoja_vida_id=int(hv_id))
    return perfiles.first()


def _desactualizado(perfil, vacantes):
    calculados = AjusteVacante.objects.filter(perfil=perfil, vacante__in=vacantes)
    if calculados.count() < vacantes.count():
        return True
    mas_antiguo = calculados.aggregate(fecha=Min("fecha"))["fecha"]
    return mas_antiguo is None or perfil.fecha_actualizacion > mas_antiguo


def calcular_ajustes(usuario, perfil, forzar=False, servicio=None):
    """HU08: ejecuta el Matcher sobre las vacantes activas y guarda el ajuste de cada una."""
    vacantes = Vacante.objects.filter(activa=True)
    if not forzar and not _desactualizado(perfil, vacantes):
        return False
    datos = [{"id": v.pk, "titulo": v.titulo, "descripcion": v.descripcion, "requisitos": v.requisitos}
             for v in vacantes]
    resultado = (servicio or CopilotoService()).ejecutar(
        usuario, "buscar_vacantes", hoja_vida_id=perfil.hoja_vida_id, perfil=perfil.datos, vacantes=datos
    )
    if resultado.get("error"):
        raise RuntimeError(resultado["error"])
    with transaction.atomic():
        for ajuste in resultado.get("ajustes", []):
            AjusteVacante.objects.update_or_create(
                perfil=perfil, vacante_id=ajuste["vacante_id"],
                defaults={"score": ajuste["score"], "cumple": ajuste["cumple"], "no_cumple": ajuste["no_cumple"],
                          "fecha": timezone.now()},
            )
    return True


def filtrar_vacantes(ciudad="", modalidad="", salario_min=None, salario_max=None):
    """HU09: filtros por ciudad, modalidad y rango salarial, resueltos en la base de datos."""
    vacantes = Vacante.objects.filter(activa=True)
    if ciudad:
        vacantes = vacantes.filter(ciudad__iexact=ciudad)
    if modalidad:
        vacantes = vacantes.filter(modalidad=modalidad)
    if salario_min is not None:
        vacantes = vacantes.filter(salario_max__gte=salario_min)
    if salario_max is not None:
        vacantes = vacantes.filter(salario_min__lte=salario_max)
    return vacantes


def rango_salarial():
    return Vacante.objects.filter(activa=True).aggregate(minimo=Min("salario_min"), maximo=Max("salario_max"))


def umbral_alerta():
    return getattr(settings, "ALERTAS_UMBRAL_AJUSTE", UMBRAL_ALERTA_DEFECTO)


def generar_alertas(usuario, umbral=None, servicio=None):
    """HU11: crea una alerta por cada vacante activa con ajuste >= umbral que el candidato no había recibido.

    Reutiliza el ajuste del Matcher (solo recalcula si el perfil o las vacantes cambiaron).
    Devuelve la lista de alertas nuevas.
    """
    perfil = perfil_activo(usuario)
    if perfil is None:
        return []
    calcular_ajustes(usuario, perfil, servicio=servicio)
    umbral = umbral_alerta() if umbral is None else umbral
    ya_avisadas = AlertaVacante.objects.filter(usuario=usuario).values_list("vacante_id", flat=True)
    candidatas = (AjusteVacante.objects.filter(perfil=perfil, score__gte=umbral, vacante__activa=True)
                  .exclude(vacante_id__in=ya_avisadas).select_related("vacante"))
    return [AlertaVacante.objects.create(usuario=usuario, vacante=a.vacante, score=a.score) for a in candidatas]


def generar_alertas_todos(umbral=None):
    """Ejecución periódica (comando generar_alertas): revisa a todos los candidatos con perfil."""
    candidatos = Usuario.objects.filter(is_active=True, rol=Usuario.Rol.CANDIDATO,
                                        hojas_vida__perfil__isnull=False).distinct()
    total = 0
    for usuario in candidatos:
        try:
            total += len(generar_alertas(usuario, umbral=umbral))
        except (CuotaAgotada, RuntimeError):  # sin cuota o fallo del grafo: se intenta en la próxima ejecución
            continue
    return total


def alertas_pendientes(usuario):
    return AlertaVacante.objects.filter(usuario=usuario, leida=False, vacante__activa=True).count()
