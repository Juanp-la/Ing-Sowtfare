"""Reglas deterministas que convierten el texto de la HV en un borrador de perfil (sin inventar nada)."""
import re

from core.dominio.texto import normalizar
from core.llm.esquemas import perfil_vacio

SECCIONES = {
    "resumen": ("perfil", "resumen", "perfil profesional", "acerca de mi", "sobre mi", "objetivo", "objetivo profesional"),
    "experiencia": ("experiencia", "experiencia laboral", "experiencia profesional"),
    "educacion": ("educacion", "formacion", "formacion academica", "estudios"),
    "habilidades": ("habilidades", "competencias", "conocimientos", "habilidades tecnicas", "herramientas"),
    "idiomas": ("idiomas", "lenguas"),
}
CIUDADES = ("Medellín", "Bogotá", "Cali", "Barranquilla", "Cartagena", "Bucaramanga", "Pereira", "Manizales",
            "Cúcuta", "Ibagué", "Santa Marta", "Villavicencio", "Pasto", "Montería", "Neiva", "Armenia",
            "Envigado", "Itagüí", "Bello", "Rionegro", "Sabaneta", "Soacha", "Popayán", "Tunja", "Valledupar")

_CORREO = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_TELEFONO = re.compile(r"\+?\d[\d\s()-]{7,}\d")
_RANGO_ANIOS = re.compile(r"(?:19|20)\d{2}\s*[-–]\s*(?:19|20)\d{2}")
_EXPERIENCIA = re.compile(r"^(?P<cargo>.+?)\s+[-–|]\s+(?P<empresa>.+?)\s*\((?P<periodo>[^)]*)\)\s*$")
_EDUCACION = re.compile(r"^(?P<titulo>.+?)\s+[-–|]\s+(?P<institucion>.+?)(?:\s*\((?P<anio>[^)]*)\))?\s*$")
_ANIO = re.compile(r"\b(?:19|20)\d{2}\b")
_SEPARADORES = re.compile(r"[,;•·|\n]")


def _seccion(linea):
    clave = normalizar(linea).strip(" :")
    for nombre, encabezados in SECCIONES.items():
        if clave in encabezados:
            return nombre
    return None


def _lista(lineas):
    elementos = []
    for parte in _SEPARADORES.split("\n".join(lineas)):
        parte = parte.strip(" -*\t")
        if parte and parte not in elementos:
            elementos.append(parte)
    return elementos


def _telefono(texto):
    """Primer número con 7 o más dígitos que no sea un rango de años."""
    for m in _TELEFONO.finditer(_CORREO.sub(" ", texto)):
        valor = m.group(0).strip()
        if len(re.sub(r"\D", "", valor)) >= 7 and not _RANGO_ANIOS.fullmatch(valor):
            return valor
    return ""


def _nombre(cabecera):
    for linea in cabecera:
        if "@" not in linea and not _TELEFONO.search(linea) and "|" not in linea and len(linea.split()) <= 6:
            return linea.title() if linea.isupper() else linea
    return ""


def _ciudad(cabecera):
    texto = normalizar(" ".join(cabecera))
    for ciudad in CIUDADES:
        if re.search(rf"\b{re.escape(normalizar(ciudad))}\b", texto):
            return ciudad
    return ""


def _experiencia(lineas):
    entradas = []
    for linea in lineas:
        m = _EXPERIENCIA.match(linea)
        if m:
            entradas.append({**{k: v.strip() for k, v in m.groupdict().items()}, "descripcion": ""})
        elif entradas:
            entradas[-1]["descripcion"] = f"{entradas[-1]['descripcion']} {linea}".strip()
        else:
            entradas.append({"cargo": linea, "empresa": "", "periodo": "", "descripcion": ""})
    return entradas


def _educacion(lineas):
    entradas = []
    for linea in lineas:
        m = _EDUCACION.match(linea)
        if m:
            entradas.append({"titulo": m["titulo"].strip(), "institucion": m["institucion"].strip(),
                             "anio": (m["anio"] or "").strip()})
        else:
            anio = _ANIO.search(linea)
            entradas.append({"titulo": linea, "institucion": "", "anio": anio.group(0) if anio else ""})
    return entradas


def parsear_hv(texto):
    perfil = perfil_vacio()
    cabecera, bloques, actual = [], {}, None
    for bruta in (texto or "").splitlines():
        linea = bruta.strip()
        if not linea:
            continue
        nueva = _seccion(linea)
        if nueva:
            actual = nueva
            bloques.setdefault(actual, [])
        elif actual:
            bloques[actual].append(linea)
        else:
            cabecera.append(linea)

    correo = _CORREO.search(texto or "")
    perfil["contacto"] = {
        "nombre": _nombre(cabecera),
        "email": correo.group(0) if correo else "",
        "telefono": _telefono("\n".join(cabecera)) or _telefono(texto or ""),
        "ciudad": _ciudad(cabecera),
    }
    perfil["resumen"] = " ".join(bloques.get("resumen", []))
    perfil["experiencia"] = _experiencia(bloques.get("experiencia", []))
    perfil["educacion"] = _educacion(bloques.get("educacion", []))
    perfil["habilidades"] = _lista(bloques.get("habilidades", []))
    perfil["idiomas"] = _lista(bloques.get("idiomas", []))
    return perfil
