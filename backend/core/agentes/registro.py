"""Registro de nodos del grafo. Cada feature registra los suyos desde apps/<app>/agentes.py:

    registrar_nodo("extractor", AgenteExtractor, intenciones=["extraer_perfil"], orden=10)

`fabrica` es cualquier callable fabrica(llm=..., trazador=...) que devuelva el nodo
(una subclase de AgenteBase sirve directamente). Dentro de una intención los nodos
corren en orden ascendente.
"""
from dataclasses import dataclass
from typing import Callable

RESERVADOS = {"control_cuota", "supervisor"}


@dataclass(frozen=True)
class NodoRegistrado:
    nombre: str
    fabrica: Callable
    intenciones: tuple
    orden: int = 100


_REGISTRO = {}


def registrar_nodo(nombre, fabrica, *, intenciones, orden=100):
    if nombre in RESERVADOS:
        raise ValueError(f"El nombre de nodo '{nombre}' está reservado por el núcleo.")
    if not intenciones:
        raise ValueError("Un nodo debe atender al menos una intención.")
    _REGISTRO[nombre] = NodoRegistrado(nombre, fabrica, tuple(intenciones), orden)


def eliminar_nodo(nombre):
    _REGISTRO.pop(nombre, None)


def nodos_registrados():
    return sorted(_REGISTRO.values(), key=lambda n: (n.orden, n.nombre))


def nodos_para(intencion):
    return [n for n in nodos_registrados() if intencion in n.intenciones]


def intenciones():
    return sorted({i for n in _REGISTRO.values() for i in n.intenciones})


def instantanea():
    return dict(_REGISTRO)


def restaurar(copia):
    _REGISTRO.clear()
    _REGISTRO.update(copia)
