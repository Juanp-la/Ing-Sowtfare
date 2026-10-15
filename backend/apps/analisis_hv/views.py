from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from core.models import HojaVida, PerfilExtraido

from . import servicios
from .extractor_texto import ErrorLecturaHV
from .forms import CargaHVForm, PerfilForm


def _hv_del_usuario(request, pk):
    return get_object_or_404(HojaVida, pk=pk, usuario=request.user)


@login_required
def lista(request):
    """Mis hojas de vida: lista desde BD con acciones por registro (ver, editar perfil, eliminar)."""
    hojas = HojaVida.objects.filter(usuario=request.user).select_related("perfil")
    return render(request, "analisis_hv/lista.html", {"hojas": hojas})


@login_required
def cargar(request):
    """HU02: carga de HV en PDF o Word de máximo 5 MB."""
    form = CargaHVForm(request.POST, request.FILES) if request.method == "POST" else CargaHVForm()
    if form.is_bound and form.is_valid():
        hv = servicios.cargar_hv(request.user, form.cleaned_data["archivo"], form.formato)
        messages.success(request, f"Archivo cargado: {hv.nombre_archivo}")
        return redirect("analisis_hv:detalle", pk=hv.pk)
    return render(request, "analisis_hv/cargar.html", {"form": form})


@login_required
def detalle(request, pk):
    hv = _hv_del_usuario(request, pk)
    perfil = PerfilExtraido.objects.filter(hoja_vida=hv).first()
    return render(request, "analisis_hv/detalle.html", {"hv": hv, "perfil": perfil,
                                                        "mensaje_ilegible": servicios.MENSAJE_ILEGIBLE})


@login_required
@require_POST
def analizar(request, pk):
    """Ejecuta el agente Extractor + validador de veracidad y abre el perfil editable (HU03)."""
    hv = _hv_del_usuario(request, pk)
    try:
        _, validacion = servicios.analizar_hv(request.user, hv)
    except ErrorLecturaHV:
        messages.error(request, servicios.MENSAJE_ILEGIBLE)
        return redirect("analisis_hv:detalle", pk=hv.pk)
    rechazados = validacion.get("rechazados", [])
    if rechazados:
        messages.warning(request, f"El validador descartó {len(rechazados)} dato(s) que no aparecen en tu hoja de vida.")
    messages.info(request, "Revisa los datos extraídos y confirma para guardarlos.")
    return redirect("analisis_hv:perfil", pk=hv.pk)


@login_required
def perfil(request, pk):
    """HU03: ver y corregir el perfil extraído; solo se guarda al confirmar."""
    hv = _hv_del_usuario(request, pk)
    perfil_extraido = PerfilExtraido.objects.filter(hoja_vida=hv).first()
    if perfil_extraido is None:
        return render(request, "analisis_hv/perfil.html", {"hv": hv, "form": None})

    if request.method == "POST":
        form = PerfilForm(request.POST)
        if form.is_valid() and request.POST.get("accion") == "confirmar":
            servicios.confirmar_perfil(perfil_extraido, form.a_perfil())
            messages.success(request, "Perfil confirmado y guardado.")
            return redirect("analisis_hv:lista")
        sin_guardar = form.is_valid()
    else:
        form = PerfilForm(initial=PerfilForm.iniciales(perfil_extraido.datos))
        sin_guardar = False
    return render(request, "analisis_hv/perfil.html",
                  {"hv": hv, "perfil": perfil_extraido, "form": form, "sin_guardar": sin_guardar})


@login_required
def eliminar(request, pk):
    """NF02: elimina la HV con todos sus datos a solicitud del candidato."""
    hv = _hv_del_usuario(request, pk)
    if request.method == "POST":
        servicios.eliminar_hv(hv)
        messages.success(request, "La hoja de vida y todos sus datos fueron eliminados.")
        return redirect("analisis_hv:lista")
    return render(request, "analisis_hv/eliminar.html", {"hv": hv})
