"""Cifrado de campos y archivos con Fernet (NF02).

La clave sale de la variable de entorno CAMPOS_CIFRADO_KEY. Sin clave, solo en DEBUG
o en pruebas se genera una clave efímera en memoria (nunca se escribe en disco).
"""
import logging
import sys

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)
_fernet = None


def _en_pruebas():
    return "pytest" in sys.modules


def obtener_fernet():
    global _fernet
    if _fernet is None:
        clave = settings.CAMPOS_CIFRADO_KEY
        if not clave:
            if not (settings.DEBUG or _en_pruebas()):
                raise ImproperlyConfigured("Defina CAMPOS_CIFRADO_KEY (ver .env.example).")
            logger.warning("CAMPOS_CIFRADO_KEY no definida: se usa una clave efímera de desarrollo.")
            clave = Fernet.generate_key()
        _fernet = Fernet(clave)
    return _fernet


def reiniciar():
    """Olvida la clave cargada (pruebas o rotación)."""
    global _fernet
    _fernet = None


def cifrar(texto):
    return obtener_fernet().encrypt(str(texto).encode("utf-8")).decode("ascii")


def descifrar(token):
    try:
        return obtener_fernet().decrypt(str(token).encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        logger.warning("No se pudo descifrar un campo (clave distinta o dato alterado).")
        return None


def cifrar_bytes(contenido):
    return obtener_fernet().encrypt(contenido)


def descifrar_bytes(contenido):
    try:
        return obtener_fernet().decrypt(contenido)
    except InvalidToken:
        logger.warning("No se pudo descifrar un archivo (clave distinta o dato alterado).")
        return None
