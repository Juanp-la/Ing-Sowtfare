"""Caché en memoria de respuestas del LLM (NF01: evita repetir llamadas idénticas)."""
import hashlib
import json
import threading
from collections import OrderedDict
from dataclasses import replace

from .base import LLMClient


class LLMConCache(LLMClient):
    def __init__(self, cliente, max_items=256):
        self.cliente = cliente
        self.modelo = cliente.modelo
        self.max_items = max_items
        self._datos = OrderedDict()
        self._lock = threading.Lock()

    def _clave(self, prompt, esquema, borrador):
        base = json.dumps([esquema.__name__, prompt, borrador], ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def generar(self, prompt, esquema, *, borrador=None):
        clave = self._clave(prompt, esquema, borrador)
        with self._lock:
            if clave in self._datos:
                self._datos.move_to_end(clave)
                # Una respuesta en caché no consume tokens de la cuota.
                return replace(self._datos[clave], tokens=0, desde_cache=True)
        respuesta = self.cliente.generar(prompt, esquema, borrador=borrador)
        with self._lock:
            self._datos[clave] = respuesta
            while len(self._datos) > self.max_items:
                self._datos.popitem(last=False)
        return respuesta
