from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.http import require_POST

from core.models import HVAdaptada, Vacante

from . import servicios


def _url_opcional(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:  # la otra feature puede no estar instalada en esta rama
        return None


def _adaptacion_del_usuario(request, pk):
    return get_object_or_404(HVAdaptada.objects.select_related("vacante", "hoja_vida"),
                             pk=pk, hoja_vida__usuario=request.user)


@login_required
def inicio(request):
    """Lista de vacantes (BD) con «Adaptar mi HV» y la lista de mis adaptaciones con sus acciones."""
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    adaptaciones = (HVAdaptada.objects.filter(hoja_vida__usuario=request.user)
                    .select_related("vacante", "hoja_vida"))
    return render(request, "adaptacion_hv/inicio.html", {
        "perfil": perfil, "perfiles": servicios.perfiles_del_usuario(request.user),
        "vacantes": Vacante.objects.filter(activa=True).order_by("titulo"), "adaptaciones": adaptaciones,
        "url_cargar": _url_opcional("analisis_hv:cargar"),
    })


@login_required
def vacante(request, pk):
    """Confirma la vacante y la HV antes de pedir la propuesta al Redactor."""
    vacante_obj = get_object_or_404(Vacante, pk=pk, activa=True)
    perfil = servicios.perfil_activo(request.user, request.GET.get("hv"))
    pendiente = None
    if perfil is not None:
        pendiente = HVAdaptada.objects.filter(hoja_vida=perfil.hoja_vida, vacante=vacante_obj).first()
    return render(request, "adaptacion_hv/vacante.html", {
        "vacante": vacante_obj, "perfil": perfil, "perfiles": servicios.perfiles_del_usuario(request.user),
        "anterior": pendiente, "url_cargar": _url_opcional("analisis_hv:cargar"),
    })


@login_required
@require_POST
def generar(request, pk):
    """HU12: el agente Redactor propone la adaptación de la HV a la vacante."""
    vacante_obj = get_object_or_404(Vacante, pk=pk, activa=True)
    perfil = servicios.perfil_activo(request.user, request.POST.get("hv"))
    if perfil is None:
        messages.warning(request, "Necesitas una hoja de vida analizada para adaptarla.")
        return redirect("adaptacion_hv:vacante", pk=pk)
    try:
        adaptacion = servicios.adaptar(request.user, perfil, vacante_obj)
    except servicios.ErrorAdaptacion:
        messages.error(request, "El Redactor no pudo adaptar tu hoja de vida. Intenta de nuevo.")
        return redirect("adaptacion_hv:vacante", pk=pk)
    if not adaptacion.cambios:
        messages.info(request, "Tu hoja de vida ya está bien orientada a esta vacante: no hay cambios que proponer.")
    else:
        messages.success(request, f"El Redactor propuso {len(adaptacion.cambios)} cambio(s). Revísalos y decide.")
    return redirect("adaptacion_hv:comparar", pk=adaptacion.pk)


@login_required
def comparar(request, pk):
    """HU13 (original y adaptada lado a lado) + HU14 (aprobar o rechazar cada cambio antes de aplicar)."""
    adaptacion = _adaptacion_del_usuario(request, pk)
    error = None
    if request.method == "POST":
        if adaptacion.estado != HVAdaptada.Estado.PENDIENTE:
            messages.info(request, "Esta adaptación ya fue decidida.")
            return redirect("adaptacion_hv:comparar", pk=pk)
        decisiones = {c["id"]: request.POST.get(f"decision_{c['id']}", "") for c in adaptacion.cambios}
        try:
            aprobados = servicios.decidir(adaptacion, decisiones)
        except ValueError as exc:
            error = str(exc)
        else:
            if aprobados:
                messages.success(request, f"Aplicamos {aprobados} cambio(s) aprobado(s). Tu HV original no se modificó.")
            else:
                messages.info(request, "Rechazaste todos los cambios: la adaptación quedó descartada.")
            return redirect("adaptacion_hv:comparar", pk=pk)
    return render(request, "adaptacion_hv/comparar.html", {
        "adaptacion": adaptacion, "filas": servicios.comparacion(adaptacion), "error": error,
        "perfil_original": adaptacion.hoja_vida.perfil.datos,
        "url_postular": _url_opcional("postulaciones:nueva", adaptacion.vacante_id),
    })


@login_required
def eliminar(request, pk):
    adaptacion = _adaptacion_del_usuario(request, pk)
    if request.method == "POST":
        adaptacion.delete()
        messages.success(request, "Adaptación eliminada.")
        return redirect("adaptacion_hv:inicio")
    return render(request, "adaptacion_hv/eliminar.html", {"adaptacion": adaptacion})


@login_required
def descargar(request, pk):
    adaptacion = _adaptacion_del_usuario(request, pk)
    if adaptacion.estado != HVAdaptada.Estado.APLICADA:
        raise Http404("Solo se descarga una adaptación aplicada.")
    respuesta = HttpResponse(
        servicios.documento_word(adaptacion),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="hv_adaptada_{adaptacion.pk}.docx"'
    return respuesta
