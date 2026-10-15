"""Comparación requisito por requisito entre un perfil y una vacante.

Lo usan el Matcher (cumplo / no cumplo) y el Coach (brechas). Es determinista y explica
cada resultado con una evidencia tomada del perfil.
Formato de requisito: {"tipo": habilidad|experiencia|educacion|idioma, "valor": str,
"obligatorio": bool, "anios": int opcional}.
"""
import re
from datetime import date

from .texto import normalizar, palabras

NIVELES_EDUCACION = [
    (7, ("doctor",)),
    (6, ("maestria", "magister", "master")),
    (5, ("especializacion", "especialista")),
    (4, ("profesional", "ingenier", "licenciad", "pregrado", "administrador de empresas", "economista", "contador")),
    (3, ("tecnolog",)),
    (2, ("tecnic",)),
    (1, ("bachiller",)),
]
NOMBRE_NIVEL = {1: "bachiller", 2: "técnico", 3: "tecnólogo", 4: "profesional", 5: "especialización",
                6: "maestría", 7: "doctorado"}
NIVELES_IDIOMA = ["a1", "a2", "b1", "b2", "c1", "c2"]
_ANIO = re.compile(r"(19|20)\d{2}")
_NIVEL_IDIOMA = re.compile(r"\b([abc][12])\b")


def nivel_educativo(texto):
    t = normalizar(texto)
    for nivel, claves in NIVELES_EDUCACION:
        if any(c in t for c in claves):
            return nivel
    return 0


def anios_periodo(periodo, hoy=None):
    """'2022 - 2025' -> 3; '2021 - actual' -> años hasta hoy; sin años -> 0."""
    t = normalizar(periodo)
    anios = [int(m.group(0)) for m in _ANIO.finditer(t)]
    if not anios:
        return 0
    inicio = anios[0]
    if len(anios) > 1:
        fin = anios[1]
    elif any(p in t for p in ("actual", "presente", "hoy")):
        fin = (hoy or date.today()).year
    else:
        fin = inicio
    return max(0, fin - inicio)


def _contiene(a, b):
    """True si las palabras del texto más corto aparecen seguidas dentro del más largo."""
    pa, pb = palabras(a), palabras(b)
    if not pa or not pb:
        return False
    corto, largo = (pa, pb) if len(pa) <= len(pb) else (pb, pa)
    n = len(corto)
    return any(largo[i:i + n] == corto for i in range(len(largo) - n + 1))


def _idioma(texto):
    t = normalizar(texto)
    m = _NIVEL_IDIOMA.search(t)
    nivel = NIVELES_IDIOMA.index(m.group(1)) if m else -1
    nombre = _NIVEL_IDIOMA.sub("", t).strip()
    return nombre, nivel


def evaluar_requisito(perfil, requisito, hoy=None):
    perfil = perfil or {}
    tipo = requisito.get("tipo", "habilidad")
    valor = requisito.get("valor", "")
    resultado = {"tipo": tipo, "requisito": valor, "obligatorio": bool(requisito.get("obligatorio")),
                 "cumple": False, "evidencia": ""}

    if tipo == "educacion":
        exigido = nivel_educativo(valor)
        mejor = max((nivel_educativo(e.get("titulo", "")) for e in perfil.get("educacion", [])), default=0)
        resultado["cumple"] = mejor >= exigido > 0
        resultado["evidencia"] = (f"Nivel en la HV: {NOMBRE_NIVEL.get(mejor, 'no declarado')}; "
                                  f"se pide: {NOMBRE_NIVEL.get(exigido, valor)}")
        return resultado

    if tipo == "idioma":
        nombre_req, nivel_req = _idioma(valor)
        for idioma in perfil.get("idiomas", []):
            nombre, nivel = _idioma(idioma)
            if nombre and nombre_req and (nombre in nombre_req or nombre_req in nombre):
                resultado["cumple"] = nivel >= nivel_req
                resultado["evidencia"] = f"Idioma declarado: {idioma}"
                return resultado
        resultado["evidencia"] = "El idioma no aparece en la hoja de vida"
        return resultado

    if tipo == "experiencia":
        exigidos = int(requisito.get("anios") or 0)
        relacionados = [e for e in perfil.get("experiencia", [])
                        if _contiene(valor, f"{e.get('cargo', '')} {e.get('descripcion', '')}")]
        total = sum(anios_periodo(e.get("periodo", ""), hoy) for e in relacionados)
        resultado["cumple"] = bool(relacionados) and total >= exigidos
        if relacionados:
            cargos = ", ".join(e.get("cargo", "") for e in relacionados)
            resultado["evidencia"] = f"{total} año(s) en cargos relacionados ({cargos}); se piden {exigidos}"
        else:
            resultado["evidencia"] = f"Sin experiencia relacionada con «{valor}»; se piden {exigidos} año(s)"
        return resultado

    # habilidad (por defecto)
    for habilidad in perfil.get("habilidades", []):
        if _contiene(valor, habilidad):
            resultado["cumple"] = True
            resultado["evidencia"] = f"Habilidad declarada: {habilidad}"
            return resultado
    for exp in perfil.get("experiencia", []):
        if _contiene(valor, f"{exp.get('cargo', '')} {exp.get('descripcion', '')}"):
            resultado["cumple"] = True
            resultado["evidencia"] = f"Mencionada en la experiencia como {exp.get('cargo', '')}"
            return resultado
    resultado["evidencia"] = "No aparece en la hoja de vida"
    return resultado


def evaluar_requisitos(perfil, requisitos, hoy=None):
    """Devuelve (cumple, no_cumple), cada uno con la evidencia del requisito."""
    cumple, no_cumple = [], []
    for requisito in requisitos or []:
        r = evaluar_requisito(perfil, requisito, hoy)
        (cumple if r["cumple"] else no_cumple).append(r)
    return cumple, no_cumple
