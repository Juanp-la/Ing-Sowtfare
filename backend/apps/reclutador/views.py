from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from core.models import Postulacion

from . import servicios
from .forms import DecisionForm, FiltroCandidatosForm
from .permisos import reclutador_requerido


@reclutador_requerido
def inicio(request):
    """Mis vacantes publicadas con cuántos candidatos hay y cuántos faltan por revisar."""
    return render(request, "reclutador/inicio.html", {"vacantes": servicios.vacantes_del_reclutador(request.user)})


@reclutador_requerido
def candidatos(request, pk):
    """HU19: candidatos postulados a la vacante ordenados por ajuste, con la acción «Evaluar»."""
    vacante = servicios.vacante_visible(request.user, pk)
    if vacante is None:
        raise Http404("Vacante no encontrada.")
    form = FiltroCandidatosForm(request.GET or None)
    estado = form.cleaned_data.get("estado", "") if form.is_valid() else ""
    return render(request, "reclutador/candidatos.html", {
        "vacante": vacante, "form": form, "postulaciones": servicios.candidatos_por_ajuste(vacante, estado),
        "total_requisitos": len(vacante.requisitos),
    })


@reclutador_requerido
def evaluar(request, pk):
    """HU20: ver el perfil enviado y marcar apto o no apto con un comentario para el candidato."""
    postulacion = get_object_or_404(Postulacion.objects.select_related("vacante", "usuario"), pk=pk)
    if servicios.vacante_visible(request.user, postulacion.vacante_id) is None:
        raise Http404("Postulación no encontrada.")
    if request.method == "POST":
        form = DecisionForm(request.POST)
        if form.is_valid():
            servicios.decidir(request.user, postulacion, form.cleaned_data["decision"], form.cleaned_data["comentario"])
            messages.success(request, f"Marcaste a {postulacion.usuario.nombre_visible} como "
                                      f"{postulacion.get_estado_display().lower()}. El candidato ya ve tu retroalimentación.")
            return redirect("reclutador:candidatos", pk=postulacion.vacante_id)
    else:
        servicios.abrir_para_revision(postulacion)
        inicial = {"decision": postulacion.estado, "comentario": postulacion.comentario_reclutador} \
            if postulacion.decidida else None
        form = DecisionForm(initial=inicial)
    return render(request, "reclutador/evaluar.html", {"p": postulacion, "perfil": postulacion.perfil_enviado,
                                                       "form": form})
