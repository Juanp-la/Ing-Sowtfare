from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from core.models import AjusteVacante, Vacante

from . import servicios
from .forms import FiltroVacantesForm


def _url_opcional(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:  # la feature puede no estar instalada en esta rama
        return None


@login_required
def lista(request):
    """HU08 + HU09: vacantes desde la BD ordenadas por ajuste, con filtros y "Ver ajuste" por registro."""
    perfiles = servicios.perfiles_del_usuario(request.user)
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    form = FiltroVacantesForm(request.GET or None)
    contexto = {"form": form, "perfil": perfil, "perfiles": perfiles, "filas": [], "error": None,
                "url_cargar": _url_opcional("analisis_hv:cargar")}
    if perfil is None:
        return render(request, "matching_vacantes/lista.html", contexto)

    try:
        servicios.calcular_ajustes(request.user, perfil)
    except RuntimeError:
        contexto["error"] = "No fue posible calcular el ajuste de las vacantes. Intenta de nuevo."
        return render(request, "matching_vacantes/lista.html", contexto)

    filtros = form.cleaned_data if form.is_bound and form.is_valid() else {}
    vacantes = servicios.filtrar_vacantes(
        ciudad=filtros.get("ciudad", ""), modalidad=filtros.get("modalidad", ""),
        salario_min=filtros.get("salario_min"), salario_max=filtros.get("salario_max"),
    )
    contexto["filas"] = (AjusteVacante.objects.filter(perfil=perfil, vacante__in=vacantes)
                         .select_related("vacante").order_by("-score", "vacante__titulo"))
    contexto["total_vacantes"] = Vacante.objects.filter(activa=True).count()
    return render(request, "matching_vacantes/lista.html", contexto)


@login_required
@require_POST
def recalcular(request):
    perfil = servicios.perfil_activo(request.user, request.POST.get("hv"))
    if perfil:
        servicios.calcular_ajustes(request.user, perfil, forzar=True)
        messages.success(request, "Ajuste recalculado con tu perfil actual.")
    destino = reverse("matching_vacantes:lista")
    return redirect(f"{destino}?{urlencode({'hv': perfil.hoja_vida_id})}" if perfil else destino)


@login_required
def detalle(request, pk):
    """HU10: requisitos que cumplo y no cumplo, requisito por requisito."""
    vacante = get_object_or_404(Vacante, pk=pk, activa=True)
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    ajuste = None
    if perfil is not None:
        servicios.calcular_ajustes(request.user, perfil)
        ajuste = AjusteVacante.objects.filter(perfil=perfil, vacante=vacante).first()
    total = len(vacante.requisitos)
    return render(request, "matching_vacantes/detalle.html", {
        "vacante": vacante, "perfil": perfil, "ajuste": ajuste, "total": total,
        "url_preparar": _url_opcional("preparacion:vacante", vacante.pk),
        "url_cargar": _url_opcional("analisis_hv:cargar"),
    })
