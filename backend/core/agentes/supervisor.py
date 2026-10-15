from langgraph.graph import END

from . import registro
from .base import AgenteBase


class Supervisor(AgenteBase):
    """Router por intención: elige el primer nodo registrado para la intención pedida."""

    nombre = "supervisor"

    def decidir_ruta(self, estado):
        nodos = registro.nodos_para(estado.get("intencion", ""))
        return nodos[0].nombre if nodos else END

    def ejecutar(self, estado):
        ruta = self.decidir_ruta(estado)
        if ruta == END:
            return {"ruta": END, "error": "intencion_no_disponible"}
        return {"ruta": ruta}
