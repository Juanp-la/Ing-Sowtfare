"""Adaptador hacia Magneto (patrón Adapter). En el Sprint 2 solo existe el cliente simulado."""
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


class MagnetoClient(ABC):
    """Interfaz que cumplirá el cliente real cuando Magneto exponga su API."""

    @abstractmethod
    def autenticar(self, email, clave):
        """Devuelve PerfilMagneto si las credenciales son válidas; si no, None."""

    @abstractmethod
    def obtener_perfil(self, magneto_id):
        """Devuelve el PerfilMagneto de una cuenta o None."""


class MagnetoMockClient(MagnetoClient):
    """Simula Magneto sin red.

    Directorio de cuentas sintéticas:
    - `cuentas=[{"magneto_id", "nombre", "email", "clave_hash"}]` en memoria (pruebas), o
    - por defecto, las cuentas con magneto_id que crea `manage.py seed_demo`.
    """

    def __init__(self, cuentas=None):
        self._cuentas = None if cuentas is None else {c["email"].lower(): c for c in cuentas}

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


def obtener_cliente_magneto():
    if settings.MAGNETO_CLIENT == "mock":
        return MagnetoMockClient()
    raise ImproperlyConfigured("En el Sprint 2 solo existe el cliente simulado (MAGNETO_CLIENT=mock).")
