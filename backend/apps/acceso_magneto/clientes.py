"""Adaptador hacia Magneto (patrón Adapter). Solo existe el cliente simulado: Magneto no expone API pública.

Sprint 3 agrega a la interfaz la HV guardada en el perfil (HU04) y la postulación a una vacante (HU15).
"""
import hashlib
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ImproperlyConfigured


@dataclass(frozen=True)
class PerfilMagneto:
    magneto_id: str
    nombre: str
    email: str


@dataclass(frozen=True)
class ArchivoHVMagneto:
    """Hoja de vida que el candidato ya tiene en su perfil de Magneto."""

    nombre: str
    formato: str  # "pdf" o "docx"
    contenido: bytes
    actualizada: str = ""

    @property
    def huella(self):
        return hashlib.sha256(self.contenido).hexdigest()


class ErrorMagneto(Exception):
    """Magneto rechazó la operación o no respondió."""


class MagnetoClient(ABC):
    """Interfaz que cumplirá el cliente real cuando Magneto exponga su API."""

    @abstractmethod
    def autenticar(self, email, clave):
        """Devuelve PerfilMagneto si las credenciales son válidas; si no, None."""

    @abstractmethod
    def obtener_perfil(self, magneto_id):
        """Devuelve el PerfilMagneto de una cuenta o None."""

    @abstractmethod
    def obtener_hv(self, magneto_id):
        """HU04: devuelve el ArchivoHVMagneto guardado en el perfil o None si no tiene."""

    @abstractmethod
    def postular(self, magneto_id, vacante_magneto_id, perfil):
        """HU15: registra la postulación en Magneto y devuelve su identificador."""


class MagnetoMockClient(MagnetoClient):
    """Simula Magneto sin red.

    Directorio de cuentas sintéticas:
    - `cuentas=[{"magneto_id", "nombre", "email", "clave_hash"}]` en memoria (pruebas), o
    - por defecto, las cuentas con magneto_id que crea `manage.py seed_demo`.
    `hojas_vida={magneto_id: ArchivoHVMagneto}` reemplaza las HV sintéticas de `core.datos_demo`.
    """

    def __init__(self, cuentas=None, hojas_vida=None, fallar_postulacion=False):
        self._cuentas = None if cuentas is None else {c["email"].lower(): c for c in cuentas}
        self._hojas_vida = hojas_vida
        self.fallar_postulacion = fallar_postulacion
        self.postulaciones = []

    def _desde_bd(self, **filtro):
        from core.models import Usuario

        usuario = Usuario.objects.filter(magneto_id__isnull=False, is_active=True, **filtro).first()
        if usuario is None:
            return None
        return {"magneto_id": usuario.magneto_id, "nombre": usuario.nombre_visible,
                "email": usuario.email, "clave_hash": usuario.password}

    def _buscar_por_email(self, email):
        if self._cuentas is not None:
            return self._cuentas.get(email.lower())
        return self._desde_bd(email__iexact=email)

    def autenticar(self, email, clave):
        cuenta = self._buscar_por_email((email or "").strip())
        if not cuenta or not clave or not check_password(clave, cuenta["clave_hash"]):
            return None
        return PerfilMagneto(cuenta["magneto_id"], cuenta["nombre"], cuenta["email"])

    def obtener_perfil(self, magneto_id):
        if self._cuentas is not None:
            cuenta = next((c for c in self._cuentas.values() if c["magneto_id"] == magneto_id), None)
        else:
            cuenta = self._desde_bd(magneto_id=magneto_id)
        return PerfilMagneto(cuenta["magneto_id"], cuenta["nombre"], cuenta["email"]) if cuenta else None

    def obtener_hv(self, magneto_id):
        if not magneto_id:
            return None
        if self._hojas_vida is not None:
            return self._hojas_vida.get(magneto_id)
        from core.datos_demo import HV_EN_MAGNETO
        from core.pruebas.fabricas import pdf_bytes

        datos = HV_EN_MAGNETO.get(magneto_id)
        if datos is None:
            return None
        return ArchivoHVMagneto(datos["nombre"], "pdf", pdf_bytes(datos["texto"]), datos["actualizada"])

    def postular(self, magneto_id, vacante_magneto_id, perfil):
        if self.fallar_postulacion or not magneto_id or not vacante_magneto_id:
            raise ErrorMagneto("Magneto no aceptó la postulación")
        identificador = f"MAG-P-{uuid.uuid4().hex[:10].upper()}"
        self.postulaciones.append({"id": identificador, "candidato": magneto_id, "vacante": vacante_magneto_id})
        return identificador


_override = None


def establecer_cliente_magneto(cliente):
    """Inyección para pruebas (None restablece el cliente por configuración)."""
    global _override
    _override = cliente


def obtener_cliente_magneto():
    if _override is not None:
        return _override
    if settings.MAGNETO_CLIENT == "mock":
        return MagnetoMockClient()
    raise ImproperlyConfigured("Solo existe el cliente simulado de Magneto (MAGNETO_CLIENT=mock).")
