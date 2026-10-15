import json
import time

from .base import LLMClient, RespuestaLLM, estimar_tokens


class MockLLMClient(LLMClient):
    """LLM falso y determinista (LLM_PROVIDER=mock). No hace llamadas de red.

    - Devuelve el `borrador` validado contra el esquema (misma entrada -> misma salida).
    - `respuestas={"NombreEsquema": dict | callable(prompt, borrador)}` fuerza una salida
      (útil para simular que el modelo inventa datos).
    - `latencia_s` simula un modelo lento (pruebas de NF01).
    """

    modelo = "mock-determinista"

    def __init__(self, respuestas=None, latencia_s=0.0):
        self.respuestas = respuestas or {}
        self.latencia_s = latencia_s
        self.llamadas = []

    def generar(self, prompt, esquema, *, borrador=None):
        if self.latencia_s:
            time.sleep(self.latencia_s)
        forzada = self.respuestas.get(esquema.__name__)
        if callable(forzada):
            datos = forzada(prompt, borrador)
        elif forzada is not None:
            datos = forzada
        else:
            datos = borrador or {}
        objeto = esquema.model_validate(datos)
        salida = objeto.model_dump_json()
        self.llamadas.append({"esquema": esquema.__name__, "prompt": prompt})
        tokens = estimar_tokens(prompt) + estimar_tokens(json.dumps(borrador or {}, default=str)) + estimar_tokens(salida)
        return RespuestaLLM(datos=objeto, tokens=tokens, modelo=self.modelo)
