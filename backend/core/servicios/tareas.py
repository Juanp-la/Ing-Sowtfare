"""Ejecución en segundo plano sin bloquear la interfaz (NF01).

Con COPILOTO_TAREAS_ASINCRONAS=1 la tarea corre en un hilo y la vista responde de inmediato;
con 0 (pruebas) corre en línea. No requiere broker: suficiente para el MVP local.
"""
import logging
import threading

from django.conf import settings
from django.db import close_old_connections

logger = logging.getLogger(__name__)


def _envolver(funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except Exception:  # la tarea debe dejar su propio estado de error; aquí solo se registra
        logger.exception("Falló una tarea en segundo plano")
    finally:
        close_old_connections()


def lanzar(funcion, *args, **kwargs):
    if settings.COPILOTO_TAREAS_ASINCRONAS:
        hilo = threading.Thread(target=_envolver, args=(funcion, *args), kwargs=kwargs, daemon=True)
        hilo.start()
        return hilo
    funcion(*args, **kwargs)
    return None
