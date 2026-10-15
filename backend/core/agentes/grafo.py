"""GrafoCopiloto: arma el StateGraph de LangGraph con los nodos que las features registraron.

START -> control_cuota -(sin cupo)-> END
                       -(ok)-> supervisor -(ruta por intención)-> nodo1 -> nodo2 -> ... -> END
Un nodo que deja `error` en el estado corta la ruta.
"""
import uuid

from langgraph.graph import END, START, StateGraph

from ..servicios.cuota import ControlCuota
from . import registro
from .estado import EstadoCopiloto
from .supervisor import Supervisor
from .trazador import Trazador


class GrafoCopiloto:
    def __init__(self, llm=None, trazador=None, control_cuota=None):
        from ..llm.fabrica import obtener_llm

        self.llm = llm or obtener_llm()
        self.trazador = trazador or Trazador()
        self.control_cuota = control_cuota or ControlCuota()

    def _nodo_control_cuota(self, estado):
        usuario_id = estado.get("usuario_id")
        if usuario_id is None:
            return {"cuota_ok": True}
        from ..models import Usuario

        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario is None or not self.control_cuota.verificar(usuario):
            return {"cuota_ok": False, "error": "cuota_agotada"}
        return {"cuota_ok": True}

    @staticmethod
    def _siguiente(nombre):
        def decidir(estado):
            if estado.get("error"):
                return END
            ruta = [n.nombre for n in registro.nodos_para(estado.get("intencion", ""))]
            if nombre in ruta and ruta.index(nombre) + 1 < len(ruta):
                return ruta[ruta.index(nombre) + 1]
            return END

        return decidir

    def construir(self):
        nodos = registro.nodos_registrados()
        destinos = [n.nombre for n in nodos] + [END]
        grafo = StateGraph(EstadoCopiloto)
        grafo.add_node("control_cuota", self._nodo_control_cuota)
        grafo.add_node("supervisor", Supervisor(llm=self.llm, trazador=self.trazador))
        for nodo in nodos:
            grafo.add_node(nodo.nombre, nodo.fabrica(llm=self.llm, trazador=self.trazador))
        grafo.add_edge(START, "control_cuota")
        grafo.add_conditional_edges(
            "control_cuota", lambda e: "supervisor" if e.get("cuota_ok") else END, ["supervisor", END]
        )
        grafo.add_conditional_edges("supervisor", lambda e: e.get("ruta") or END, destinos)
        for nodo in nodos:
            grafo.add_conditional_edges(nodo.nombre, self._siguiente(nodo.nombre), destinos)
        return grafo.compile()

    def invocar(self, estado):
        estado = {"traza": [], "tokens_usados": 0, **estado}
        estado.setdefault("ejecucion_id", uuid.uuid4().hex)
        return self.construir().invoke(estado)
