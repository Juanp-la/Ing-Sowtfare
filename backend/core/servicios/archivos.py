"""Archivos de HV cifrados en disco (NF02). El nombre en disco es aleatorio."""
import uuid

from django.core.files.base import ContentFile

from .cifrado import cifrar_bytes, descifrar_bytes


def guardar_archivo_hv(hoja_vida, contenido):
    hoja_vida.archivo.save(f"{uuid.uuid4().hex}.enc", ContentFile(cifrar_bytes(contenido)), save=False)
    hoja_vida.tamano_bytes = len(contenido)


def leer_archivo_hv(hoja_vida):
    if not hoja_vida.archivo:
        return None
    with hoja_vida.archivo.open("rb") as f:
        return descifrar_bytes(f.read())
