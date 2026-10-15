"""Nodo Matcher (intención "buscar_vacantes"): supervisor -> matcher -> END.

Ajuste = 70 % reglas (requisito por requisito, los obligatorios pesan doble) + 30 % similitud
local de texto (Embedder inyectable). Determinista y sin llamadas al LLM.
"""
from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo
from core.dominio.requisitos import evaluar_requisitos
from core.dominio.texto import texto_perfil

from .embedder import obtener_embedder

PESO_REGLAS = 0.7
PESO_SIMILITUD = 0.3


def puntaje_reglas(cumple, no_cumple):
    def peso(r):
        return 2 if r["obligatorio"] else 1

    total = sum(peso(r) for r in cumple + no_cumple)
    return sum(peso(r) for r in cumple) / total if total else 0.0


def texto_vacante(vacante):
    requisitos = " ".join(r.get("valor", "") for r in vacante.get("requisitos", []))
    return f"{vacante.get('titulo', '')} {vacante.get('descripcion', '')} {requisitos}"


class AgenteMatcher(AgenteBase):
    nombre = "matcher"

    def __init__(self, llm=None, trazador=None, embedder=None):
        super().__init__(llm=llm, trazador=trazador)
        self.embedder = embedder or obtener_embedder()

    def ejecutar(self, estado):
        perfil = estado.get("perfil") or {}
        texto = texto_perfil(perfil)
        ajustes = []
        for vacante in estado.get("vacantes", []):
            cumple, no_cumple = evaluar_requisitos(perfil, vacante.get("requisitos", []))
            reglas = puntaje_reglas(cumple, no_cumple)
            similitud = self.embedder.similitud(texto, texto_vacante(vacante))
            ajustes.append({
                "vacante_id": vacante["id"],
                "score": round(100 * (PESO_REGLAS * reglas + PESO_SIMILITUD * similitud), 1),
                "reglas": round(reglas, 3),
                "similitud": round(similitud, 3),
                "cumple": cumple,
                "no_cumple": no_cumple,
            })
        ajustes.sort(key=lambda a: (-a["score"], a["vacante_id"]))
        return {"ajustes": ajustes}


registrar_nodo("matcher", AgenteMatcher, intenciones=["buscar_vacantes"], orden=30)
