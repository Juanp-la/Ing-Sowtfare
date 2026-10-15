from django.db import transaction

from core.models import HojaVida, PerfilExtraido
from core.servicios.archivos import guardar_archivo_hv, leer_archivo_hv
from core.servicios.copiloto import CopilotoService

from .extractor_texto import ErrorLecturaHV, obtener_extractor

MENSAJE_ILEGIBLE = "No fue posible leer el archivo, intente con otro formato"


def cargar_hv(usuario, archivo, formato):
    """HU02: guarda la HV cifrada en disco (NF02) y la deja lista para analizar."""
    archivo.seek(0)
    hv = HojaVida(usuario=usuario, nombre_archivo=archivo.name[:255], formato=formato)
    guardar_archivo_hv(hv, archivo.read())
    hv.save()
    return hv


def analizar_hv(usuario, hv, servicio=None):
    """Extrae el texto (Strategy) y ejecuta el grafo: extractor -> validador de veracidad (NF03).

    Devuelve (perfil, validacion). Lanza ErrorLecturaHV si el archivo no se puede leer.
    """
    if not hv.texto_extraido:
        contenido = leer_archivo_hv(hv)
        try:
            if contenido is None:
                raise ErrorLecturaHV("archivo no disponible")
            hv.texto_extraido = obtener_extractor(hv.formato).extraer(contenido)
        except ErrorLecturaHV:
            hv.estado = HojaVida.Estado.ERROR
            hv.save(update_fields=["estado"])
            raise
        hv.save(update_fields=["texto_extraido"])

    resultado = (servicio or CopilotoService()).ejecutar(
        usuario, "extraer_perfil", hoja_vida_id=hv.pk, texto_hv=hv.texto_extraido
    )
    if resultado.get("error") or "perfil" not in resultado:
        hv.estado = HojaVida.Estado.ERROR
        hv.save(update_fields=["estado"])
        raise ErrorLecturaHV(resultado.get("error", "sin perfil"))

    with transaction.atomic():
        perfil, _ = PerfilExtraido.objects.update_or_create(
            hoja_vida=hv, defaults={"datos": resultado["perfil"], "confirmado": False}
        )
        hv.estado = HojaVida.Estado.ANALIZADA
        hv.save(update_fields=["estado"])
    return perfil, resultado.get("validacion", {})


def confirmar_perfil(perfil, datos):
    """HU03: solo aquí se guardan los cambios del candidato."""
    perfil.datos = datos
    perfil.confirmado = True
    perfil.save()
    return perfil


def eliminar_hv(hv):
    """NF02: borra la HV, su archivo cifrado y todo lo derivado (perfil, diagnósticos, ajustes, planes)."""
    hv.delete()
