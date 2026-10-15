"""Elige el cliente LLM según LLM_PROVIDER (mock por defecto) y permite inyectarlo en pruebas."""
from django.conf import settings

from .cache import LLMConCache
from .langchain_adapter import LangChainLLMClient
from .mock import MockLLMClient

_override = None
_compartido = None


def establecer_llm(cliente):
    global _override
    _override = cliente


def restablecer_llm():
    global _override, _compartido
    _override = None
    _compartido = None


def crear_llm():
    proveedor = settings.LLM_PROVIDER
    cliente = MockLLMClient() if proveedor == "mock" else LangChainLLMClient(proveedor, settings.LLM_MODEL)
    return LLMConCache(cliente) if settings.LLM_CACHE else cliente


def obtener_llm():
    global _compartido
    if _override is not None:
        return _override
    if _compartido is None:
        _compartido = crear_llm()
    return _compartido
