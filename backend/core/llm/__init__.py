"""Acceso al LLM: interfaz LLMClient, cliente falso determinista y adaptador LangChain apagado."""
from .base import LLMClient, RespuestaLLM, estimar_tokens
from .fabrica import obtener_llm
from .mock import MockLLMClient

__all__ = ["LLMClient", "MockLLMClient", "RespuestaLLM", "estimar_tokens", "obtener_llm"]
