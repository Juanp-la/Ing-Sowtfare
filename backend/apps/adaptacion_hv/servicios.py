import copy
import difflib
import io

from django.db import transaction
from django.utils import timezone

from core.models import HVAdaptada, PerfilExtraido
from core.servicios.copiloto import CopilotoService

from .agentes import etiqueta_experiencia

APROBAR, RECHAZAR = "aprobar", "rechazar"


class ErrorAdaptacion(Exception):
    """El agente Redactor no pudo proponer la adaptación."""


def perfiles_del_usuario(usuario):
    return (PerfilExtraido.objects.filter(hoja_vida__usuario=usuario)
            .select_related("hoja_vida").order_by("-confirmado", "-hoja_vida__fecha_carga", "-id"))


def perfil_activo(usuario, hv_id=None):
    perfiles = perfiles_del_usuario(usuario)
    if hv_id and str(hv_id).isdigit():
        perfiles = perfiles.filter(hoja_vida_id=int(hv_id))
    return perfiles.first()


def _vacante_como_dict(vacante):
    return {"id": vacante.pk, "titulo": vacante.titulo, "empresa": vacante.empresa,
            "descripcion": vacante.descripcion, "requisitos": vacante.requisitos}


def adaptar(usuario, perfil, vacante, servicio=None):
    """HU12: el Redactor propone cambios para la vacante; quedan pendientes hasta que el candidato decida."""
    hv = perfil.hoja_vida
    resultado = (servicio or CopilotoService()).ejecutar(
        usuario, "adaptar_hv", hoja_vida_id=hv.pk, vacante_id=vacante.pk, perfil=perfil.datos,
        texto_hv=hv.texto_extraido, vacante=_vacante_como_dict(vacante),
    )
    if resultado.get("error") or "adaptacion" not in resultado.get("datos", {}):
        raise ErrorAdaptacion(resultado.get("error", "sin resultado"))
    cambios = [{**c, "decision": ""} for c in resultado["datos"]["adaptacion"]]
    with transaction.atomic():
        HVAdaptada.objects.filter(hoja_vida=hv, vacante=vacante, estado=HVAdaptada.Estado.PENDIENTE).delete()
        return HVAdaptada.objects.create(hoja_vida=hv, vacante=vacante, cambios=cambios,
                                         ejecucion_id=resultado.get("ejecucion_id", ""),
                                         perfil_adaptado=copy.deepcopy(perfil.datos))


def aplicar_cambio(perfil, cambio):
    """Aplica un cambio aprobado sobre una copia del perfil."""
    seccion, propuesta = cambio["seccion"], cambio["propuesta"]
    if seccion == "resumen":
        perfil["resumen"] = propuesta
    elif seccion == "habilidades":
        perfil["habilidades"] = list(propuesta)
    elif seccion == "palabras_clave":
        perfil["palabras_clave"] = list(propuesta)
    elif seccion == "experiencia":
        por_etiqueta = {etiqueta_experiencia(e): e for e in perfil.get("experiencia", [])}
        nuevas = [por_etiqueta[e] for e in propuesta if e in por_etiqueta]
        restantes = [e for e in perfil.get("experiencia", []) if e not in nuevas]
        perfil["experiencia"] = nuevas + restantes
    return perfil


def decidir(adaptacion, decisiones):
    """HU14: guarda la decisión de cada cambio y aplica solo los aprobados.

    `decisiones` = {id_cambio: "aprobar" | "rechazar"}. Todo cambio debe tener decisión.
    El perfil original (PerfilExtraido) nunca se modifica: el resultado queda en HVAdaptada.perfil_adaptado.
    """
    cambios = adaptacion.cambios
    faltantes = [c["titulo"] for c in cambios if decisiones.get(c["id"]) not in (APROBAR, RECHAZAR)]
    if faltantes:
        raise ValueError(f"Falta decidir: {', '.join(faltantes)}")
    perfil = copy.deepcopy(adaptacion.hoja_vida.perfil.datos)
    for cambio in cambios:
        cambio["decision"] = decisiones[cambio["id"]]
        if cambio["decision"] == APROBAR:
            perfil = aplicar_cambio(perfil, cambio)
    adaptacion.cambios = cambios
    adaptacion.perfil_adaptado = perfil
    aprobados = sum(1 for c in cambios if c["decision"] == APROBAR)
    adaptacion.estado = HVAdaptada.Estado.APLICADA if aprobados else HVAdaptada.Estado.DESCARTADA
    adaptacion.fecha_decision = timezone.now()
    adaptacion.save()
    return aprobados


def _resaltar(original, propuesta):
    """Marca las palabras nuevas de la propuesta para la vista lado a lado (HU13)."""
    a, b = original.split(), propuesta.split()
    partes = []
    for op, _, _, j1, j2 in difflib.SequenceMatcher(a=a, b=b).get_opcodes():
        texto = " ".join(b[j1:j2])
        if texto:
            partes.append({"texto": texto, "nuevo": op != "equal"})
    return partes


def comparacion(adaptacion):
    """HU13: original y propuesta de cada cambio, con lo que cambia marcado."""
    filas = []
    for cambio in adaptacion.cambios:
        original, propuesta = cambio["original"], cambio["propuesta"]
        fila = {**cambio, "es_lista": isinstance(propuesta, list)}
        if fila["es_lista"]:
            original = original or []
            fila["original_items"] = [{"texto": t, "posicion": i + 1} for i, t in enumerate(original)]
            fila["propuesta_items"] = [
                {"texto": t, "nuevo": t not in original,
                 "movido": t in original and original.index(t) != i} for i, t in enumerate(propuesta)]
        else:
            fila["propuesta_partes"] = _resaltar(original or "", propuesta or "")
        filas.append(fila)
    return filas


def documento_word(adaptacion):
    """Exporta la HV adaptada (solo cambios aprobados) a .docx."""
    from docx import Document

    perfil = adaptacion.perfil_adaptado
    contacto = perfil.get("contacto", {})
    documento = Document()
    documento.add_heading(contacto.get("nombre") or "Hoja de vida", level=0)
    datos = " | ".join(v for v in (contacto.get("ciudad"), contacto.get("email"), contacto.get("telefono")) if v)
    if datos:
        documento.add_paragraph(datos)
    if perfil.get("resumen"):
        documento.add_heading("Perfil", level=1)
        documento.add_paragraph(perfil["resumen"])
    if perfil.get("experiencia"):
        documento.add_heading("Experiencia", level=1)
        for exp in perfil["experiencia"]:
            documento.add_paragraph(etiqueta_experiencia(exp), style="List Bullet")
            if exp.get("descripcion"):
                documento.add_paragraph(exp["descripcion"])
    if perfil.get("educacion"):
        documento.add_heading("Educación", level=1)
        for edu in perfil["educacion"]:
            documento.add_paragraph(" - ".join(v for v in (edu.get("titulo"), edu.get("institucion"), edu.get("anio")) if v),
                                    style="List Bullet")
    for titulo, llave in (("Habilidades", "habilidades"), ("Idiomas", "idiomas"), ("Palabras clave", "palabras_clave")):
        if perfil.get(llave):
            documento.add_heading(titulo, level=1)
            documento.add_paragraph(", ".join(perfil[llave]))
    salida = io.BytesIO()
    documento.save(salida)
    return salida.getvalue()
