"""AgenteBase (patrón Template Method): __call__ mide, ejecuta y deja traza; cada agente implementa ejecutar()."""
import logging
import time
from abc import ABC, abstractmethod

from ..llm.fabrica import obtener_llm
from .trazador import Trazador

logger = logging.getLogger(__name__)

LLAVES_CONTROL = ("traza", "tokens_usados")


class AgenteBase(ABC):
    nombre = "agente"

    def __init__(self, llm=None, trazador=None):
        self.llm = llm or obtener_llm()
        self.trazador = trazador or Trazador()
        self._tokens = 0

    def __call__(self, estado):
        inicio = time.perf_counter()
        self._tokens = 0
        try:
            actualizacion = dict(self.ejecutar(estado) or {})
            resultado = "ok"
        except Exception as exc:  # un agente que falla no tumba la aplicación: queda trazado
            logger.error("Falló el agente %s: %s", self.nombre, type(exc).__name__)
            actualizacion = {"error": f"{self.nombre}: {type(exc).__name__}"}
            resultado = "error"
        duracion_ms = int((time.perf_counter() - inicio) * 1000)
        registro = self.trazador.registrar(
            agente=self.nombre,
            entrada={k: v for k, v in estado.items() if k not in LLAVES_CONTROL},
            salida=actualizacion,
            tokens=self._tokens,
            duracion_ms=duracion_ms,
            estado=resultado,
            contexto=estado,
        )
        actualizacion["traza"] = [*estado.get("traza", []), registro]
        actualizacion["tokens_usados"] = estado.get("tokens_usados", 0) + self._tokens
        return actualizacion

    def consultar_llm(self, prompt, esquema, borrador=None):
        """Llama al LLM con salida estructurada y acumula los tokens del nodo."""
        respuesta = self.llm.generar(prompt, esquema, borrador=borrador)
        self._tokens += respuesta.tokens
        return respuesta.datos

    @abstractmethod
    def ejecutar(self, estado):
        """Devuelve un dict con las llaves de EstadoCopiloto que este agente actualiza."""
