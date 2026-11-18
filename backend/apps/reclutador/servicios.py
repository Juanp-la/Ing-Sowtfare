from django.db.models import Count, Q

from core.models import Postulacion, Vacante

from .permisos import es_reclutador

SUGERENCIAS = {
    "habilidad": "Fortalece esta habilidad con un curso corto y muéstrala en un proyecto de portafolio.",
    "experiencia": "Suma experiencia demostrable (práctica, proyecto o voluntariado) y escribe los resultados.",
    "educacion": "Pregunta si aceptan experiencia equivalente o planea la formación que pide el cargo.",
    "idioma": "Practica el idioma y certifica el nivel con un examen reconocido.",
}


def vacantes_del_reclutador(usuario):
    """Las vacantes que publicó el reclutador (el administrador ve todas) con el conteo de postulados."""
    vacantes = Vacante.objects.all() if usuario.rol == "admin" or usuario.is_superuser else \
        Vacante.objects.filter(reclutador=usuario)
    return vacantes.annotate(
        postulados=Count("postulaciones"),
        pendientes=Count("postulaciones", filter=Q(postulaciones__estado__in=Postulacion.ABIERTOS)),
    ).order_by("-activa", "titulo")


def vacante_visible(usuario, pk):
    return vacantes_del_reclutador(usuario).filter(pk=pk).first()


def candidatos_por_ajuste(vacante, estado=""):
    """HU19: postulados de la vacante, del mayor al menor ajuste (empate: el que se postuló primero)."""
    postulaciones = vacante.postulaciones.select_related("usuario", "hv_adaptada")
    if estado:
        postulaciones = postulaciones.filter(estado=estado)
    return postulaciones.order_by("-score", "fecha", "id")


def abrir_para_revision(postulacion):
    """Al abrir la postulación el candidato ve «En revisión» en su seguimiento (HU18)."""
    if postulacion.estado == Postulacion.Estado.ENVIADA:
        postulacion.estado = Postulacion.Estado.EN_REVISION
        postulacion.save(update_fields=["estado", "fecha_actualizacion"])


def retroalimentacion_para(postulacion, decision, comentario):
    """HU20: la decisión alimenta la retroalimentación del candidato.

    Si es «no apto», cada requisito no cumplido trae una sugerencia concreta; si es «apto», se le indica
    qué lo hizo destacar.
    """
    if decision == Postulacion.Estado.APTO:
        return [{"requisito": r["requisito"], "sugerencia": "Fue uno de tus puntos fuertes para el reclutador."}
                for r in postulacion.cumple if r.get("obligatorio")][:5]
    retro = [{"requisito": r["requisito"], "sugerencia": SUGERENCIAS.get(r.get("tipo"), SUGERENCIAS["habilidad"])}
             for r in sorted(postulacion.no_cumple, key=lambda r: not r.get("obligatorio"))]
    if not retro and comentario:
        retro = [{"requisito": "Comentario del reclutador", "sugerencia": comentario}]
    return retro


def decidir(reclutador, postulacion, decision, comentario=""):
    """HU20: marca al candidato como apto o no apto y deja la retroalimentación."""
    if not es_reclutador(reclutador):
        raise PermissionError("Solo un reclutador puede decidir.")
    if decision not in (Postulacion.Estado.APTO, Postulacion.Estado.NO_APTO):
        raise ValueError("Decisión no válida.")
    postulacion.estado = decision
    postulacion.comentario_reclutador = comentario.strip()
    postulacion.retroalimentacion = retroalimentacion_para(postulacion, decision, comentario.strip())
    postulacion.save()
    return postulacion
