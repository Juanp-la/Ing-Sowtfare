"""Rúbrica 0-100 determinista y configurable (HU05, HU06, HU07).

Cada criterio devuelve la fracción lograda (0..1), la evidencia tomada del perfil y, si
corresponde, un hallazgo con prioridad y acción sugerida. Los pesos se pueden cambiar con
settings.RUBRICA_PESOS = {"clave": peso, ...} (deben sumar 100).
"""
import re
from dataclasses import dataclass
from typing import Callable

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_NIVEL_IDIOMA = re.compile(r"\b[ABC][12]\b", re.IGNORECASE)
_LOGRO = re.compile(r"\d+\s*%|\b(?!(?:19|20)\d{2}\b)\d{2,}\b")


@dataclass(frozen=True)
class Criterio:
    clave: str
    nombre: str
    peso: int
    evaluar: Callable


def _hallazgo(categoria, descripcion, prioridad, accion):
    return {"categoria": categoria, "descripcion": descripcion, "prioridad": prioridad, "accion_sugerida": accion}


def _contacto(perfil):
    contacto = perfil.get("contacto", {})
    etiquetas = {"nombre": "nombre", "email": "correo", "telefono": "teléfono", "ciudad": "ciudad"}
    presentes = [k for k in etiquetas if str(contacto.get(k, "")).strip()]
    faltan = [etiquetas[k] for k in etiquetas if k not in presentes]
    fraccion = len(presentes) / len(etiquetas)
    if not faltan:
        return fraccion, "Nombre, correo, teléfono y ciudad presentes", None
    prioridad = "alta" if {"correo", "teléfono"} & set(faltan) else "media"
    return fraccion, f"Faltan: {', '.join(faltan)}", _hallazgo(
        "Contacto", f"Datos de contacto incompletos ({', '.join(faltan)}).", prioridad,
        "Agrega tus datos de contacto para que el reclutador pueda comunicarse contigo.")


def _resumen(perfil):
    resumen = str(perfil.get("resumen", "")).strip()
    if not resumen:
        return 0, "Sin perfil profesional", _hallazgo(
            "Perfil profesional", "La hoja de vida no tiene un perfil profesional.", "alta",
            "Escribe 2 o 3 líneas sobre quién eres, tu experiencia y el cargo que buscas.")
    if len(resumen) < 60 or len(resumen) > 600:
        return 0.5, f"Perfil de {len(resumen)} caracteres", _hallazgo(
            "Perfil profesional", "El perfil profesional es muy corto o muy largo.", "media",
            "Ajusta el perfil a entre 60 y 600 caracteres, enfocado en el cargo objetivo.")
    return 1, f"Perfil profesional de {len(resumen)} caracteres", None


def _experiencia(perfil):
    entradas = perfil.get("experiencia", [])
    if not entradas:
        return 0, "Sin experiencia registrada", _hallazgo(
            "Experiencia", "No se encontró experiencia laboral.", "alta",
            "Incluye prácticas, voluntariados o proyectos con cargo, lugar y fechas.")
    completas = [e for e in entradas if e.get("cargo") and e.get("empresa") and e.get("periodo")]
    evidencia = f"{len(completas)} de {len(entradas)} experiencia(s) con cargo, empresa y periodo"
    fraccion = min(1, len(completas) / 2)
    if len(completas) < len(entradas):
        return fraccion, evidencia, _hallazgo(
            "Experiencia", "Hay experiencias sin empresa o sin periodo.", "media",
            "Completa la empresa y las fechas (año de inicio y fin) de cada experiencia.")
    return fraccion, evidencia, None


def _logros(perfil):
    entradas = perfil.get("experiencia", [])
    if not entradas:
        return 0, "Sin experiencia para evaluar logros", None
    con_logros = [e for e in entradas if _LOGRO.search(e.get("descripcion", ""))]
    evidencia = f"{len(con_logros)} de {len(entradas)} experiencia(s) con resultados medibles"
    if not con_logros:
        return 0, evidencia, _hallazgo(
            "Logros", "Las experiencias describen tareas pero no resultados medibles.", "media",
            "Agrega cifras: porcentajes, cantidades atendidas o tiempos mejorados.")
    return len(con_logros) / len(entradas), evidencia, None


def _educacion(perfil):
    entradas = perfil.get("educacion", [])
    if not entradas:
        return 0, "Sin formación registrada", _hallazgo(
            "Educación", "No se encontró formación académica.", "alta",
            "Incluye tu último nivel de estudios con institución y año.")
    completa = any(e.get("titulo") and (e.get("institucion") or e.get("anio")) for e in entradas)
    if not completa:
        return 0.6, "Formación sin institución ni año", _hallazgo(
            "Educación", "La formación no indica institución ni año.", "baja",
            "Agrega la institución y el año de grado.")
    return 1, f"{len(entradas)} registro(s) de formación con institución o año", None


def _habilidades(perfil, minimo=8):
    habilidades = perfil.get("habilidades", [])
    if not habilidades:
        return 0, "Sin habilidades", _hallazgo(
            "Habilidades", "No se listan habilidades.", "alta",
            "Agrega al menos 8 habilidades técnicas y blandas relacionadas con tu cargo objetivo.")
    evidencia = f"{len(habilidades)} habilidad(es): {', '.join(habilidades[:5])}{'…' if len(habilidades) > 5 else ''}"
    if len(habilidades) < minimo:
        return len(habilidades) / minimo, evidencia, _hallazgo(
            "Habilidades", f"Solo se listan {len(habilidades)} habilidades.", "baja",
            f"Completa hasta {minimo} habilidades relevantes para las vacantes que buscas.")
    return 1, evidencia, None


def _idiomas(perfil):
    idiomas = perfil.get("idiomas", [])
    if not idiomas:
        return 0, "Sin idiomas", _hallazgo(
            "Idiomas", "No se indican idiomas.", "media", "Indica los idiomas que manejas y su nivel (A1 a C2).")
    if not any(_NIVEL_IDIOMA.search(i) for i in idiomas):
        return 0.6, f"Idiomas sin nivel: {', '.join(idiomas)}", _hallazgo(
            "Idiomas", "Los idiomas no indican nivel.", "baja", "Agrega el nivel según el marco europeo (A1 a C2).")
    return 1, f"Idiomas: {', '.join(idiomas)}", None


CRITERIOS_POR_DEFECTO = (
    Criterio("contacto", "Datos de contacto", 15, _contacto),
    Criterio("resumen", "Perfil profesional", 10, _resumen),
    Criterio("experiencia", "Experiencia completa", 25, _experiencia),
    Criterio("logros", "Logros medibles", 10, _logros),
    Criterio("educacion", "Educación", 15, _educacion),
    Criterio("habilidades", "Habilidades", 15, _habilidades),
    Criterio("idiomas", "Idiomas", 10, _idiomas),
)


def nivel_para(puntaje):
    if puntaje >= 75:
        return "competitivo"
    if puntaje >= 50:
        return "por_mejorar"
    return "bajo"


class Rubrica:
    def __init__(self, criterios=None, pesos=None):
        criterios = list(criterios or CRITERIOS_POR_DEFECTO)
        pesos = pesos if pesos is not None else getattr(settings, "RUBRICA_PESOS", None)
        if pesos:
            criterios = [Criterio(c.clave, c.nombre, pesos.get(c.clave, c.peso), c.evaluar) for c in criterios]
        if sum(c.peso for c in criterios) != 100:
            raise ImproperlyConfigured("Los pesos de la rúbrica deben sumar 100.")
        self.criterios = criterios

    def evaluar(self, perfil):
        detalle, hallazgos, total = [], [], 0.0
        for criterio in self.criterios:
            fraccion, evidencia, hallazgo = criterio.evaluar(perfil or {})
            obtenido = round(criterio.peso * fraccion, 1)
            total += obtenido
            detalle.append({"clave": criterio.clave, "nombre": criterio.nombre, "peso": criterio.peso,
                            "obtenido": obtenido, "evidencia": evidencia})
            if hallazgo:
                hallazgos.append(hallazgo)
        orden = {"alta": 1, "media": 2, "baja": 3}
        hallazgos.sort(key=lambda h: orden[h["prioridad"]])
        puntaje = max(0, min(100, round(total)))
        return {"puntaje": puntaje, "nivel": nivel_para(puntaje), "criterios": detalle, "hallazgos": hallazgos}
