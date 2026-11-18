from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from core.models import Postulacion, Vacante

from . import servicios
from .forms import FiltroEstadoForm


def _url_opcional(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:  # la otra feature puede no estar instalada en esta rama
        return None


def _seleccion(request, perfiles, adaptadas):
    """Lee la HV elegida: 'perfil-<id>' o 'adaptacion-<id>' (por defecto la adaptada más reciente)."""
    valor = request.POST.get("hv_enviar") or ""
    if not valor:
        if request.GET.get("adaptacion"):
            valor = f"adaptacion-{request.GET['adaptacion']}"
        elif request.GET.get("hv"):
            perfil = next((p for p in perfiles if str(p.hoja_vida_id) == request.GET["hv"]), None)
            valor = f"perfil-{perfil.pk}" if perfil else ""
    if not valor:
        valor = f"adaptacion-{adaptadas[0].pk}" if adaptadas else (f"perfil-{perfiles[0].pk}" if perfiles else "")
    return valor


@login_required
def nueva(request, pk):
    """HU15: confirmar y enviar la postulación a una vacante sin salir del copiloto."""
    vacante = get_object_or_404(Vacante, pk=pk, activa=True)
    existente = servicios.postulacion_existente(request.user, vacante)
    if existente:
        messages.info(request, "Ya te postulaste a esta vacante. Aquí puedes ver su estado.")
        return redirect("postulaciones:detalle", pk=existente.pk)
    perfiles, adaptadas = servicios.opciones_hv(request.user, vacante)
    seleccion = _seleccion(request, perfiles, adaptadas)
    error = None
    if request.method == "POST":
        tipo, _, ident = seleccion.partition("-")
        perfil = next((p for p in perfiles if tipo == "perfil" and str(p.pk) == ident), None)
        adaptacion = next((a for a in adaptadas if tipo == "adaptacion" and str(a.pk) == ident), None)
        try:
            postulacion = servicios.postular(request.user, vacante, perfil=perfil, adaptacion=adaptacion)
        except servicios.YaPostulado:
            messages.info(request, "Ya te postulaste a esta vacante.")
            return redirect("postulaciones:lista")
        except servicios.ErrorPostulacion as exc:
            error = (str(exc) if (perfil or adaptacion) is None
                     else "Magneto no recibió tu postulación. Intenta de nuevo en unos minutos.")
        else:
            messages.success(request, f"Te postulaste a {vacante.titulo}. Código en Magneto: {postulacion.magneto_id}")
            return redirect("postulaciones:detalle", pk=postulacion.pk)
    opciones = [{"valor": f"adaptacion-{a.pk}", "recomendada": True,
                 "etiqueta": f"Versión adaptada a esta vacante ({timezone.localtime(a.fecha_decision):%d/%m/%Y})"} for a in adaptadas]
    opciones += [{"valor": f"perfil-{p.pk}", "recomendada": False,
                  "etiqueta": f"{p.hoja_vida.nombre_archivo} (original)"} for p in perfiles]
    return render(request, "postulaciones/nueva.html", {
        "vacante": vacante, "perfiles": perfiles, "adaptadas": adaptadas, "opciones": opciones,
        "seleccion": seleccion, "error": error,
        "url_cargar": _url_opcional("analisis_hv:cargar"), "url_adaptar": _url_opcional("adaptacion_hv:vacante", pk),
    })


@login_required
def lista(request):
    """HU18: mis postulaciones (BD) con su estado, filtro por estado y acciones por registro."""
    form = FiltroEstadoForm(request.GET or None)
    postulaciones = Postulacion.objects.filter(usuario=request.user).select_related("vacante", "hv_adaptada")
    if form.is_valid() and form.cleaned_data.get("estado"):
        postulaciones = postulaciones.filter(estado=form.cleaned_data["estado"])
    return render(request, "postulaciones/lista.html", {
        "form": form, "postulaciones": postulaciones, "resumen": servicios.resumen_estados(request.user),
        "url_vacantes": _url_opcional("matching_vacantes:lista"),
    })


@login_required
def detalle(request, pk):
    """HU18: estado, HV enviada y la retroalimentación del reclutador cuando decide (HU20)."""
    postulacion = get_object_or_404(Postulacion.objects.select_related("vacante", "hv_adaptada", "hoja_vida"),
                                    pk=pk, usuario=request.user)
    return render(request, "postulaciones/detalle.html", {
        "p": postulacion, "url_preparar": _url_opcional("preparacion:vacante", postulacion.vacante_id),
    })


@login_required
def retirar(request, pk):
    postulacion = get_object_or_404(Postulacion.objects.select_related("vacante"), pk=pk, usuario=request.user)
    if request.method == "POST":
        try:
            servicios.retirar(postulacion)
        except servicios.ErrorPostulacion as exc:
            messages.error(request, str(exc))
            return redirect("postulaciones:detalle", pk=pk)
        messages.success(request, f"Retiraste tu postulación a {postulacion.vacante.titulo}.")
        return redirect("postulaciones:lista")
    return render(request, "postulaciones/retirar.html", {"p": postulacion})


