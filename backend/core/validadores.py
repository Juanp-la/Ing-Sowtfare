"""Validación de archivos subidos (OWASP: extensión, tamaño y firma real del archivo)."""
import io
import os
import zipfile

from django.conf import settings
from django.core.exceptions import ValidationError

MENSAJE_FORMATO_NO_ADMITIDO = "Formato no admitido: cargue un PDF o Word de máximo 5 MB"


def _es_docx(contenido):
    if not contenido.startswith(b"PK\x03\x04"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as zf:
            return "word/document.xml" in zf.namelist()
    except zipfile.BadZipFile:
        return False


def validar_archivo_hv(archivo):
    """Devuelve el formato ("pdf" o "docx") o lanza ValidationError con el mensaje de HU02."""
    extension = os.path.splitext(archivo.name or "")[1].lower()
    tamano = getattr(archivo, "size", 0) or 0
    if extension not in settings.HV_EXTENSIONES or tamano == 0 or tamano > settings.HV_TAMANO_MAXIMO:
        raise ValidationError(MENSAJE_FORMATO_NO_ADMITIDO, code="formato")

    archivo.seek(0)
    contenido = archivo.read()
    archivo.seek(0)
    if extension == ".pdf" and not contenido.startswith(b"%PDF-"):
        raise ValidationError(MENSAJE_FORMATO_NO_ADMITIDO, code="firma")
    if extension == ".docx" and not _es_docx(contenido):
        raise ValidationError(MENSAJE_FORMATO_NO_ADMITIDO, code="firma")
    return extension.lstrip(".")
