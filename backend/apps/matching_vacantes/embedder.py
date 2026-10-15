"""Interfaz Embedder (inyectable) y una implementación local sin red: bolsa de palabras + coseno."""
import math
from abc import ABC, abstractmethod
from collections import Counter

from django.conf import settings
from django.utils.module_loading import import_string

from core.dominio.texto import palabras

PALABRAS_VACIAS = {
    "con", "para", "por", "los", "las", "del", "una", "uno", "que", "como", "sus", "mas", "entre", "sin",
    "desde", "hasta", "este", "esta", "son", "tus", "mis", "años", "anos",
}


class Embedder(ABC):
    @abstractmethod
    def vectorizar(self, texto):
        """Devuelve un vector disperso {dimensión: peso}."""

    def similitud(self, texto_a, texto_b):
        a, b = self.vectorizar(texto_a), self.vectorizar(texto_b)
        producto = sum(peso * b.get(clave, 0.0) for clave, peso in a.items())
        norma = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
        return producto / norma if norma else 0.0


class EmbedderBolsaPalabras(Embedder):
    """Embedder local y determinista. Se puede reemplazar por uno semántico sin tocar el Matcher."""

    def vectorizar(self, texto):
        return dict(Counter(p for p in palabras(texto) if len(p) >= 3 and p not in PALABRAS_VACIAS))


def obtener_embedder():
    ruta = getattr(settings, "MATCHER_EMBEDDER", "")
    return import_string(ruta)() if ruta else EmbedderBolsaPalabras()
