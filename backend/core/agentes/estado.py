from typing import Any, TypedDict


class EstadoCopiloto(TypedDict, total=False):
    """Estado compartido que leen y escriben todos los nodos del grafo.

    `datos` es el punto de extensión genérico: una feature nueva guarda ahí lo propio
    sin modificar este archivo.
    """

    # Control
    intencion: str
    ruta: str
    cuota_ok: bool
    error: str
    ejecucion_id: str
    usuario_id: int
    hoja_vida_id: int
    vacante_id: int
    tokens_usados: int
    traza: list[dict[str, Any]]

    # Entradas y salidas de los agentes
    texto_hv: str
    perfil: dict[str, Any]
    validacion: dict[str, Any]
    puntaje: int
    nivel: str
    hallazgos: list[dict[str, Any]]
    criterios: list[dict[str, Any]]
    explicacion: str
    vacantes: list[dict[str, Any]]
    ajustes: list[dict[str, Any]]
    vacante: dict[str, Any]
    brechas: list[dict[str, Any]]
    preguntas: list[dict[str, Any]]
    plan: list[dict[str, Any]]

    # Extensión genérica
    datos: dict[str, Any]
