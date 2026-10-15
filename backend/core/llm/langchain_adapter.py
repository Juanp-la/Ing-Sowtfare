"""Adaptador a un LLM real vía LangChain. Apagado por defecto (LLM_PROVIDER=mock).

Solo se activa con LLM_PROVIDER y LLM_MODEL por variable de entorno; la llave la lee el
paquete del proveedor desde su propia variable de entorno. Nunca hay llaves en el código.
"""
import json

from django.core.exceptions import ImproperlyConfigured

from .base import LLMClient, RespuestaLLM, estimar_tokens


def _fabrica_por_defecto(proveedor, modelo):
    try:
        from langchain.chat_models import init_chat_model
    except ImportError as exc:  # paquete opcional
        raise ImproperlyConfigured(
            "Para un LLM real instale 'langchain' y el paquete del proveedor; o use LLM_PROVIDER=mock."
        ) from exc
    return init_chat_model(modelo, model_provider=proveedor, temperature=0)


class LangChainLLMClient(LLMClient):
    def __init__(self, proveedor, modelo, fabrica=None):
        if not modelo:
            raise ImproperlyConfigured("Defina LLM_MODEL para usar un proveedor real.")
        self.proveedor = proveedor
        self.modelo = modelo
        self._fabrica = fabrica or _fabrica_por_defecto
        self._chat = None

    def _modelo_chat(self):
        if self._chat is None:
            self._chat = self._fabrica(self.proveedor, self.modelo)
        return self._chat

    def generar(self, prompt, esquema, *, borrador=None):
        mensaje = prompt
        if borrador:
            mensaje += "\n\nBorrador calculado por reglas (respétalo; no agregues datos nuevos):\n"
            mensaje += json.dumps(borrador, ensure_ascii=False, default=str)
        estructurado = self._modelo_chat().with_structured_output(esquema, include_raw=True)
        respuesta = estructurado.invoke(mensaje)
        datos = respuesta.get("parsed")
        if datos is None:
            raise ValueError("El LLM no devolvió una salida válida para el esquema.")
        uso = getattr(respuesta.get("raw"), "usage_metadata", None) or {}
        tokens = uso.get("total_tokens") or (estimar_tokens(mensaje) + estimar_tokens(datos.model_dump_json()))
        return RespuestaLLM(datos=datos, tokens=int(tokens), modelo=self.modelo)
