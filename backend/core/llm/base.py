import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import BaseModel


def estimar_tokens(texto):
    """Aproximación estándar: ~4 caracteres por token."""
    return max(1, math.ceil(len(texto or "") / 4))


@dataclass
class RespuestaLLM:
    datos: BaseModel
    tokens: int
    modelo: str
    desde_cache: bool = False


class LLMClient(ABC):
    """Interfaz común para cualquier proveedor. Siempre devuelve salida estructurada (Pydantic).

    `borrador` es la respuesta que las reglas deterministas ya calcularon; el LLM la refina.
    """

    modelo = "desconocido"

    @abstractmethod
    def generar(self, prompt, esquema, *, borrador=None):
        """Devuelve RespuestaLLM con `datos` validados contra `esquema`."""
