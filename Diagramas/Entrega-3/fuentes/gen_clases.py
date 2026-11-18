import sys
sys.path.insert(0, ".")
from uml import clase, render

C = []
C.append(clase("AgenteBase", ["+nombre: str", "+llm: LLMClient", "+trazador: Trazador"],
               ["+__call__(estado): dict", "+consultar_llm(prompt, esquema, borrador)", "+ejecutar(estado): dict {abstract}"], "abstract"))
for n, m in [("Supervisor", ["+decidir_ruta(estado): str"]), ("AgenteExtractor", ["+ejecutar(estado)"]),
             ("AgenteEvaluador", ["+ejecutar(estado)"]), ("AgenteMatcher", ["+embedder: Embedder", "+ejecutar(estado)"]),
             ("AgenteCoach", ["+ejecutar(estado)"]), ("NodoValidador", ["+campo: str", "+ejecutar(estado)"])]:
    C.append(clase(n, [], m))
C.append(clase("AgenteRedactor", [], ["+ejecutar(estado)", "cambios_por_reglas(perfil, vacante)"], sprint3=True))
C.append(clase("ValidadorRedactor", ["+validador: ValidadorVeracidad"], ["+ejecutar(estado)"], sprint3=True))
C.append(clase("ValidadorVeracidad", ["+umbral: float = 0.8"], ["+soportado(valor, ...): bool", "+verificar(original, generado): list", "+depurar(original, generado)"]))
C.append(clase("Trazador", ["+persistir: bool"], ["+registrar(agente, entrada, salida, tokens, ms)"]))
C.append(clase("LLMClient", [], ["+generar(prompt, esquema, borrador): RespuestaLLM"], "interface"))
C.append(clase("MockLLMClient", [], []))
C.append(clase("LangChainLLMClient", [], []))
C.append(clase("LLMConCache", ["-cliente: LLMClient"], []))
C.append(clase("Embedder", [], ["+vectorizar(texto) {abstract}", "+similitud(a, b): float"], "abstract"))
C.append(clase("EmbedderBolsaPalabras", [], []))

E = """
  edge [arrowhead=empty];
  "Supervisor" -> "AgenteBase"; "AgenteExtractor" -> "AgenteBase"; "AgenteEvaluador" -> "AgenteBase";
  "AgenteMatcher" -> "AgenteBase"; "AgenteCoach" -> "AgenteBase"; "AgenteRedactor" -> "AgenteBase";
  "NodoValidador" -> "AgenteBase"; "ValidadorRedactor" -> "AgenteBase";
  "EmbedderBolsaPalabras" -> "Embedder";
  edge [arrowhead=empty, style=dashed];
  "MockLLMClient" -> "LLMClient"; "LangChainLLMClient" -> "LLMClient"; "LLMConCache" -> "LLMClient";
  edge [dir=forward, arrowhead=vee, style=solid];
  "AgenteBase" -> "LLMClient" [constraint=false, xlabel="usa"];
  "AgenteBase" -> "Trazador" [constraint=false, xlabel="traza"];
  "ValidadorVeracidad" -> "NodoValidador" [arrowhead=odiamond];
  "ValidadorVeracidad" -> "ValidadorRedactor" [arrowhead=odiamond];
  "Embedder" -> "AgenteMatcher" [arrowhead=odiamond];
  { rank=same; "LLMClient"; "Trazador"; }
"""
render("clases_agentes", "\n".join(C) + E, rankdir="TB")
