from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from core.models import Diagnostico, EjecucionAgente, HojaVida

from . import servicios

HALLAZGOS_POR_PANTALLA = 5


def _url_cargar_hv():
    try:
        return reverse("analisis_hv:cargar")
    except NoReverseMatch:  # la feature de carga puede no estar instalada en esta rama
        return None


def _diagnostico_del_usuario(request, pk):
    return get_object_or_404(Diagnostico.objects.select_related("hoja_vida"), pk=pk,
                             hoja_vida__usuario=request.user)


@login_required
def inicio(request):
    hojas = HojaVida.objects.filter(usuario=request.user).select_related("perfil").prefetch_related("diagnosticos")
    filas = [{"hv": hv, "ultimo": next(iter(hv.diagnosticos.all()), None)} for hv in hojas]
    return render(request, "diagnostico_hv/inicio.html", {"filas": filas, "url_cargar": _url_cargar_hv()})


@login_required
@require_POST
def diagnosticar(request, hv_pk):
    hv = get_object_or_404(HojaVida, pk=hv_pk, usuario=request.user)
    try:
        diagnostico = servicios.iniciar_diagnostico(request.user, hv)
    except servicios.SinPerfil:
        messages.warning(request, "Primero analiza la hoja de vida para obtener su perfil.")
        return redirect("diagnostico_hv:inicio")
    return redirect("diagnostico_hv:detalle", pk=diagnostico.pk)


@login_required
def detalle(request, pk):
    """HU05 puntaje, HU06 hallazgos (5 por pantalla), HU07 explicación, NF01 progreso y tiempos."""
    diagnostico = _diagnostico_del_usuario(request, pk)
    pagina = Paginator(diagnostico.hallazgos.all(), HALLAZGOS_POR_PANTALLA).get_page(request.GET.get("pagina"))
    return render(request, "diagnostico_hv/detalle.html", {
        "diagnostico": diagnostico,
        "pagina": pagina,
        "tiempos": servicios.tiempos_por_nodo(diagnostico),
        "estado": servicios.estado_diagnostico(diagnostico),
        "umbral": servicios.UMBRAL_SEGUNDOS,
    })


@login_required
def estado(request, pk):
    """NF01: estado en JSON para el indicador de progreso (sondeo desde el navegador)."""
    return JsonResponse(servicios.estado_diagnostico(_diagnostico_del_usuario(request, pk)))


@login_required
def trazabilidad(request):
    """NF05: qué agente se ejecutó, con qué resultado, tokens y duración."""
    ejecuciones = EjecucionAgente.objects.all() if request.user.is_staff else \
        EjecucionAgente.objects.filter(usuario=request.user)
    agentes = sorted(set(ejecuciones.values_list("agente", flat=True)))
    agente = request.GET.get("agente", "")
    if agente:
        ejecuciones = ejecuciones.filter(agente=agente)
    resumen = (ejecuciones.values("agente")
               .annotate(veces=Count("id"), tokens=Sum("tokens"), promedio_ms=Avg("duracion_ms"))
               .order_by("agente"))
    pagina = Paginator(ejecuciones.select_related("usuario"), 25).get_page(request.GET.get("pagina"))
    return render(request, "diagnostico_hv/trazabilidad.html", {
        "pagina": pagina, "resumen": resumen, "agentes": agentes, "agente": agente,
    })
