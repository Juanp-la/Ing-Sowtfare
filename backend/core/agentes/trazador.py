"""Trazador (NF05): registra cada ejecución de agente sin datos personales."""
import hashlib
import json

LLAVES_VISIBLES = {"ruta", "nivel", "error", "intencion", "puntaje"}


def resumir(salida, limite=500):
    """Resumen sin valores sensibles: tamaños y solo algunos valores de control."""
    partes = []
    for clave, valor in (salida or {}).items():
        if clave in ("traza", "tokens_usados"):
            continue
        if clave in LLAVES_VISIBLES and isinstance(valor, (str, int, float)):
            partes.append(f"{clave}={valor}")
        elif isinstance(valor, list):
            partes.append(f"{clave}[{len(valor)}]")
        elif isinstance(valor, dict):
            partes.append(f"{clave}{{{len(valor)}}}")
        elif isinstance(valor, bool):
            partes.append(f"{clave}={valor}")
        elif isinstance(valor, (int, float)):
            partes.append(f"{clave}={valor}")
        elif isinstance(valor, str):
            partes.append(f"{clave}({len(valor)} car.)")
    return "; ".join(partes)[:limite]


def hash_entrada(entrada):
    base = json.dumps(entrada, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class Trazador:
    def __init__(self, persistir=True):
        self.persistir = persistir

    def registrar(self, agente, entrada, salida, tokens, duracion_ms, estado="ok", contexto=None):
        contexto = contexto or {}
        registro = {
            "agente": agente,
            "tokens": int(tokens),
            "duracion_ms": int(duracion_ms),
            "estado": estado,
            "resumen": resumir(salida),
        }
        if self.persistir:
            from ..models import EjecucionAgente

            EjecucionAgente.objects.create(
                usuario_id=contexto.get("usuario_id"),
                hoja_vida_id=contexto.get("hoja_vida_id"),
                ejecucion_id=contexto.get("ejecucion_id", ""),
                agente=agente,
                entrada_hash=hash_entrada(entrada),
                salida_resumen=registro["resumen"],
                tokens=registro["tokens"],
                duracion_ms=registro["duracion_ms"],
                estado=estado,
            )
        return registro
