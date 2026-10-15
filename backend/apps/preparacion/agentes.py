"""Nodo Coach (intención "preparar"): supervisor -> coach -> END.

Desde la vacante y las brechas del perfil genera preguntas probables de entrevista (HU16)
y un plan de mejora con una acción concreta por cada brecha (HU17). Las reglas producen el
borrador; el LLM lo puede redactar mejor, pero el plan siempre cubre todas las brechas.
"""
from pydantic import BaseModel, Field

from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo
from core.dominio.requisitos import evaluar_requisitos

MAX_TECNICAS = 3
MAX_BRECHAS = 3

PROMPT_COACH = (
    "Eres el agente Coach de Magneto Copiloto. Con la vacante y las brechas del candidato, redacta preguntas "
    "probables de entrevista con una sugerencia de respuesta y un plan de mejora con una acción concreta, un "
    "recurso y un plazo por cada brecha. No atribuyas al candidato experiencia que no tenga.\n"
    "Vacante: {titulo} en {empresa}.\nBrechas: {brechas}"
)


class Pregunta(BaseModel):
    pregunta: str
    tipo: str = "tecnica"
    brecha: str = ""
    sugerencia: str = ""


class AccionPlan(BaseModel):
    brecha: str
    tipo: str = "habilidad"
    accion: str
    recurso: str = ""
    plazo: str = ""
    prioridad: str = "media"


class Preparacion(BaseModel):
    preguntas: list[Pregunta] = Field(default_factory=list)
    plan: list[AccionPlan] = Field(default_factory=list)


def _cargo_principal(perfil):
    experiencia = perfil.get("experiencia", [])
    return experiencia[0].get("cargo", "") if experiencia else ""


def preguntas_por_reglas(perfil, vacante, cumple, brechas):
    titulo, empresa = vacante.get("titulo", "el cargo"), vacante.get("empresa", "la empresa")
    cargo = _cargo_principal(perfil)
    preguntas = []
    for r in [r for r in cumple if r["tipo"] in ("habilidad", "experiencia")][:MAX_TECNICAS]:
        preguntas.append({
            "pregunta": f"Para {titulo} se pide {r['requisito']}. Cuéntanos un caso real en el que lo hayas aplicado: "
                        "¿qué problema resolviste y qué resultado obtuviste?",
            "tipo": "tecnica", "brecha": "",
            "sugerencia": "Responde con el método STAR (situación, tarea, acción, resultado)"
                          + (f" usando tu experiencia como {cargo}." if cargo else "."),
        })
    for r in brechas[:MAX_BRECHAS]:
        preguntas.append({
            "pregunta": f"La vacante pide {r['requisito']} y no aparece en tu hoja de vida. "
                        "¿Cómo cerrarías esa brecha en tus primeros meses?",
            "tipo": "brecha", "brecha": r["requisito"],
            "sugerencia": "Reconoce la brecha con honestidad y cuenta el plan concreto que ya empezaste.",
        })
    preguntas.append({
        "pregunta": "Háblanos de una situación difícil con un usuario o cliente y de cómo la resolviste.",
        "tipo": "conductual", "brecha": "", "sugerencia": "Elige un ejemplo real y cierra con lo que aprendiste.",
    })
    preguntas.append({
        "pregunta": f"¿Por qué te interesa trabajar en {empresa} como {titulo}?",
        "tipo": "conductual", "brecha": "",
        "sugerencia": "Relaciona la descripción de la vacante con tus intereses y tu experiencia.",
    })
    return preguntas


def accion_para(brecha):
    valor, tipo = brecha["requisito"], brecha["tipo"]
    prioridad = "alta" if brecha["obligatorio"] else "media"
    if tipo == "experiencia":
        return {"brecha": valor, "tipo": tipo, "prioridad": prioridad, "plazo": "3 a 6 meses",
                "accion": f"Gana experiencia demostrable en {valor} con un proyecto, práctica o voluntariado y registra resultados medibles.",
                "recurso": "Proyecto propio, práctica o voluntariado"}
    if tipo == "educacion":
        return {"brecha": valor, "tipo": tipo, "prioridad": prioridad, "plazo": "6 a 24 meses",
                "accion": f"Pregunta si aceptan experiencia equivalente; si no, planea estudios de nivel {valor}.",
                "recurso": "Programa técnico, tecnológico o profesional (p. ej. oferta pública)"}
    if tipo == "idioma":
        return {"brecha": valor, "tipo": tipo, "prioridad": prioridad, "plazo": "3 a 6 meses",
                "accion": f"Practica a diario hasta alcanzar {valor} y preséntate a un examen de certificación.",
                "recurso": "Curso de idiomas y examen de certificación"}
    return {"brecha": valor, "tipo": "habilidad", "prioridad": prioridad, "plazo": "4 a 6 semanas",
            "accion": f"Aprende {valor} con un curso introductorio y aplícalo en un proyecto pequeño para tu portafolio.",
            "recurso": "Curso en línea gratuito y proyecto de portafolio"}


def plan_por_reglas(brechas):
    plan = [accion_para(b) for b in brechas]
    return sorted(plan, key=lambda a: a["prioridad"] != "alta")


class AgenteCoach(AgenteBase):
    nombre = "coach"

    def ejecutar(self, estado):
        perfil = estado.get("perfil") or {}
        vacante = estado.get("vacante") or {}
        cumple, brechas = evaluar_requisitos(perfil, vacante.get("requisitos", []))
        borrador = {"preguntas": preguntas_por_reglas(perfil, vacante, cumple, brechas),
                    "plan": plan_por_reglas(brechas)}
        prompt = PROMPT_COACH.format(titulo=vacante.get("titulo", ""), empresa=vacante.get("empresa", ""),
                                     brechas=[b["requisito"] for b in brechas])
        resultado = self.consultar_llm(prompt, Preparacion, borrador=borrador)
        plan = [a.model_dump() for a in resultado.plan]
        cubiertas = {a["brecha"] for a in plan}
        plan += [accion_para(b) for b in brechas if b["requisito"] not in cubiertas]  # toda brecha tiene acción
        return {"brechas": brechas, "preguntas": [p.model_dump() for p in resultado.preguntas], "plan": plan}


registrar_nodo("coach", AgenteCoach, intenciones=["preparar"], orden=40)
