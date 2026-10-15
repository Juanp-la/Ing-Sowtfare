"""CopilotoService: fachada única entre las vistas y el motor de agentes (patrón Facade)."""
from ..agentes import registro
from ..agentes.grafo import GrafoCopiloto
from ..llm.fabrica import obtener_llm
from .cuota import ControlCuota, CuotaAgotada


class IntencionNoDisponible(Exception):
    """Ningún nodo registrado atiende la intención pedida (la feature no está instalada)."""


class CopilotoService:
    def __init__(self, llm=None, control_cuota=None, trazador=None):
        self.llm = llm
        self.control_cuota = control_cuota or ControlCuota()
        self.trazador = trazador

    def ejecutar(self, usuario, intencion, **entrada):
        """Verifica la cuota (NF04), invoca el grafo y devuelve el estado final."""
        if not registro.nodos_para(intencion):
            raise IntencionNoDisponible(intencion)
        if not self.control_cuota.verificar(usuario):
            raise CuotaAgotada("Alcanzaste tu cuota mensual de uso del copiloto.")
        estado = {"intencion": intencion, "usuario_id": usuario.pk, **entrada}
        grafo = GrafoCopiloto(llm=self.llm or obtener_llm(), trazador=self.trazador, control_cuota=self.control_cuota)
        resultado = grafo.invocar(estado)
        if resultado.get("error") == "cuota_agotada":
            raise CuotaAgotada("Alcanzaste tu cuota mensual de uso del copiloto.")
        return resultado
