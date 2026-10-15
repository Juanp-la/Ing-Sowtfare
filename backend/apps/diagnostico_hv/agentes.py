"""Nodo Evaluador (intención "diagnosticar"): supervisor -> evaluador -> END.

El puntaje, el nivel y los hallazgos salen de la rúbrica determinista; el LLM solo redacta
el resumen de la explicación (no puede cambiar el puntaje).
"""
from pydantic import BaseModel

from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo

from .rubrica import Rubrica

NIVELES = {"bajo": "bajo", "por_mejorar": "por mejorar", "competitivo": "competitivo"}

PROMPT_EVALUADOR = (
    "Eres el agente Evaluador de Magneto Copiloto. Redacta en 2 o 3 frases, en español y en segunda persona, "
    "la explicación del puntaje de la hoja de vida usando solo los criterios y la evidencia dados.\n"
    "Puntaje: {puntaje}/100 ({nivel}).\nCriterios: {criterios}"
)


class ExplicacionDiagnostico(BaseModel):
    resumen: str = ""


def borrador_explicacion(evaluacion):
    fuertes = [c["nombre"].lower() for c in evaluacion["criterios"] if c["obtenido"] >= c["peso"]]
    debiles = [c["nombre"].lower() for c in evaluacion["criterios"] if c["obtenido"] < c["peso"]]
    texto = f"Tu hoja de vida obtiene {evaluacion['puntaje']}/100 (nivel {NIVELES[evaluacion['nivel']]})."
    if fuertes:
        texto += f" Sumas todos los puntos en: {', '.join(fuertes)}."
    if debiles:
        texto += f" Puedes ganar puntos en: {', '.join(debiles)}."
    return texto


class AgenteEvaluador(AgenteBase):
    nombre = "evaluador"

    def __init__(self, llm=None, trazador=None, rubrica=None):
        super().__init__(llm=llm, trazador=trazador)
        self.rubrica = rubrica or Rubrica()

    def ejecutar(self, estado):
        evaluacion = self.rubrica.evaluar(estado.get("perfil") or {})
        prompt = PROMPT_EVALUADOR.format(puntaje=evaluacion["puntaje"], nivel=evaluacion["nivel"],
                                         criterios=evaluacion["criterios"])
        explicacion = self.consultar_llm(prompt, ExplicacionDiagnostico,
                                         borrador={"resumen": borrador_explicacion(evaluacion)})
        return {**evaluacion, "explicacion": explicacion.resumen}


registrar_nodo("evaluador", AgenteEvaluador, intenciones=["diagnosticar"], orden=20)
