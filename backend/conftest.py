"""Fixtures compartidas (NÚCLEO) para las pruebas del núcleo y de todas las features."""
import secrets
import socket

import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True, scope="session")
def _clave_cifrado_pruebas():
    from django.conf import settings

    from core.servicios import cifrado

    settings.CAMPOS_CIFRADO_KEY = Fernet.generate_key().decode()
    cifrado.reiniciar()
    yield
    cifrado.reiniciar()


@pytest.fixture(autouse=True)
def _sin_red(monkeypatch):
    """Ninguna prueba puede abrir conexiones de red."""

    def bloquear(*args, **kwargs):
        raise RuntimeError("Prueba intentó usar la red")

    monkeypatch.setattr(socket.socket, "connect", bloquear)
    monkeypatch.setattr(socket, "create_connection", bloquear)


@pytest.fixture(autouse=True)
def _entorno_pruebas(settings, tmp_path):
    from core.llm import fabrica

    settings.MEDIA_ROOT = tmp_path / "media"
    settings.LLM_PROVIDER = "mock"
    settings.LLM_CACHE = False
    settings.COPILOTO_TAREAS_ASINCRONAS = False
    settings.DEV_AUTO_LOGIN = False
    fabrica.restablecer_llm()
    yield
    fabrica.restablecer_llm()


@pytest.fixture
def registro_aislado():
    """Permite registrar nodos de prueba sin contaminar el registro global."""
    from core.agentes import registro

    copia = registro.instantanea()
    yield registro
    registro.restaurar(copia)


@pytest.fixture
def llm_falso():
    from core.llm import fabrica
    from core.llm.mock import MockLLMClient

    cliente = MockLLMClient()
    fabrica.establecer_llm(cliente)
    yield cliente
    fabrica.restablecer_llm()


@pytest.fixture
def clave():
    return secrets.token_urlsafe(12)


@pytest.fixture
def usuario(db, clave):
    from core.pruebas.fabricas import crear_usuario

    return crear_usuario(clave=clave)


@pytest.fixture
def cliente_autenticado(client, usuario):
    client.force_login(usuario)
    return client


@pytest.fixture
def hv_demo(usuario):
    from core.pruebas.fabricas import crear_hv

    return crear_hv(usuario)


@pytest.fixture
def vacantes_demo(db):
    from core.pruebas.fabricas import crear_vacantes_demo

    return crear_vacantes_demo()
