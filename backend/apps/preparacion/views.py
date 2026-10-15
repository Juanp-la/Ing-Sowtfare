from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from core.models import Vacante

from . import servicios


def _url_cargar_hv():
    try:
        return reverse("analisis_hv:cargar")
    except NoReverseMatch:  # la feature de carga puede no estar instalada en esta rama
        return None


@login_required
def inicio(request):
    """Lista de vacantes desde la BD con la acción «Preparar» por registro."""
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    vacantes = Vacante.objects.filter(activa=True).order_by("titulo")
    return render(request, "preparacion/inicio.html", {
        "perfil": perfil, "perfiles": servicios.perfiles_del_usuario(request.user), "vacantes": vacantes,
        "url_cargar": _url_cargar_hv(),
    })


@login_required
def vacante(request, pk):
    """Preparación para una vacante: brechas, preguntas probables (HU16) y plan de mejora (HU17)."""
    vacante = get_object_or_404(Vacante, pk=pk, activa=True)
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    contexto = {"vacante": vacante, "perfil": perfil, "url_cargar": _url_cargar_hv()}
    if perfil is not None:
        preguntas, plan = servicios.preparacion_guardada(perfil, vacante)
        contexto.update({"brechas": servicios.brechas(perfil, vacante), "preguntas": preguntas, "plan": plan})
    return render(request, "preparacion/vacante.html", contexto)


@login_required
@require_POST
def generar(request, pk):
    vacante = get_object_or_404(Vacante, pk=pk, activa=True)
    perfil = servicios.perfil_activo(request.user, request.POST.get("hv"))
    destino = reverse("preparacion:vacante", args=[vacante.pk])
    if perfil is None:
        return redirect(destino)
    try:
        servicios.preparar(request.user, perfil, vacante)
        messages.success(request, "El Coach generó tus preguntas y tu plan de mejora.")
    except servicios.ErrorPreparacion:
        messages.error(request, "El Coach no pudo generar la preparación. Intenta de nuevo.")
    return redirect(f"{destino}?hv={perfil.hoja_vida_id}")
