"""PoC técnica - Magneto Copiloto (equipo Los Troyanos).

Parte A: comparación de dos librerías de extracción de texto de hojas de vida en PDF.
Parte B: 'Hello World' del grafo de agentes en LangGraph (sin llamadas a un LLM real).
"""
import time
import json
import statistics

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

RUTA_HV = "/home/claude/hv_prueba.pdf"

# ---------------------------------------------------------------- HV de prueba
def crear_hv_prueba(ruta=RUTA_HV):
    c = canvas.Canvas(ruta, pagesize=letter)
    y = 730
    lineas = [
        ("Helvetica-Bold", 16, "ANA MARIA GOMEZ RESTREPO"),
        ("Helvetica", 10, "Tecnologa en Sistemas | Medellin, Antioquia | ana.gomez@correo.com"),
        ("Helvetica-Bold", 12, "PERFIL"),
        ("Helvetica", 10, "Tecnologa en sistemas con 2 anios de experiencia en soporte tecnico"),
        ("Helvetica", 10, "y mesa de ayuda. Busco rol de soporte de aplicaciones."),
        ("Helvetica-Bold", 12, "EXPERIENCIA"),
        ("Helvetica", 10, "Analista de soporte - Empresa XYZ (2023 - 2025)"),
        ("Helvetica", 10, "Atencion de incidentes de usuarios finales y escalamiento a nivel 2."),
        ("Helvetica", 10, "Auxiliar de sistemas - Empresa ABC (2022 - 2023)"),
        ("Helvetica", 10, "Mantenimiento de equipos y administracion de inventario de TI."),
        ("Helvetica-Bold", 12, "EDUCACION"),
        ("Helvetica", 10, "Tecnologia en Sistemas de Informacion - 2022"),
        ("Helvetica-Bold", 12, "HABILIDADES"),
        ("Helvetica", 10, "SQL, Windows Server, Zendesk, Excel, ingles B1"),
    ]
    for fuente, tam, texto in lineas:
        c.setFont(fuente, tam)
        c.drawString(60, y, texto)
        y -= 22
    c.save()
    return ruta


# ---------------------------------------------------------------- Parte A
CAMPOS = ["EXPERIENCIA", "EDUCACION", "HABILIDADES", "PERFIL",
          "ana.gomez@correo.com", "Zendesk", "SQL"]


def medir(nombre, funcion, repeticiones=10):
    tiempos = []
    texto = ""
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        texto = funcion()
        tiempos.append((time.perf_counter() - inicio) * 1000)
    encontrados = sum(1 for campo in CAMPOS if campo.lower() in texto.lower())
    return {
        "libreria": nombre,
        "tiempo_ms_promedio": round(statistics.mean(tiempos), 1),
        "tiempo_ms_minimo": round(min(tiempos), 1),
        "caracteres_extraidos": len(texto.strip()),
        "campos_clave_detectados": f"{encontrados}/{len(CAMPOS)}",
    }


def extraer_pdfplumber():
    import pdfplumber
    with pdfplumber.open(RUTA_HV) as pdf:
        return "\n".join((p.extract_text() or "") for p in pdf.pages)


def extraer_pymupdf():
    import pymupdf
    doc = pymupdf.open(RUTA_HV)
    texto = "\n".join(page.get_text() for page in doc)
    doc.close()
    return texto


# ---------------------------------------------------------------- Parte B
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END


class EstadoHV(TypedDict):
    texto_hv: str
    perfil: dict
    hallazgos: List[str]
    puntaje: int


def agente_extractor(estado: EstadoHV) -> EstadoHV:
    texto = estado["texto_hv"]
    perfil = {
        "tiene_correo": "@" in texto,
        "menciona_experiencia": "EXPERIENCIA" in texto.upper(),
        "menciona_educacion": "EDUCACION" in texto.upper(),
        "habilidades": [h for h in ["SQL", "Excel", "Zendesk", "Python"] if h.lower() in texto.lower()],
    }
    return {"perfil": perfil}


def agente_evaluador(estado: EstadoHV) -> EstadoHV:
    perfil = estado["perfil"]
    hallazgos, puntaje = [], 100
    if not perfil["tiene_correo"]:
        hallazgos.append("Falta un correo de contacto visible."); puntaje -= 25
    if not perfil["menciona_experiencia"]:
        hallazgos.append("No se identifica una seccion de experiencia."); puntaje -= 25
    if len(perfil["habilidades"]) < 3:
        hallazgos.append("Se declaran pocas habilidades tecnicas."); puntaje -= 15
    if not hallazgos:
        hallazgos.append("La estructura basica de la hoja de vida es correcta.")
    return {"hallazgos": hallazgos, "puntaje": puntaje}


def construir_grafo():
    grafo = StateGraph(EstadoHV)
    grafo.add_node("extractor", agente_extractor)
    grafo.add_node("evaluador", agente_evaluador)
    grafo.add_edge(START, "extractor")
    grafo.add_edge("extractor", "evaluador")
    grafo.add_edge("evaluador", END)
    return grafo.compile()


# ---------------------------------------------------------------- main
if __name__ == "__main__":
    crear_hv_prueba()

    print("== Parte A: comparacion de librerias de extraccion ==")
    resultados = [
        medir("pdfplumber", extraer_pdfplumber),
        medir("PyMuPDF", extraer_pymupdf),
    ]
    for r in resultados:
        print(json.dumps(r, ensure_ascii=False))

    print("\n== Parte B: Hello World del grafo LangGraph ==")
    app = construir_grafo()
    inicio = time.perf_counter()
    salida = app.invoke({"texto_hv": extraer_pymupdf()})
    ms = (time.perf_counter() - inicio) * 1000
    print("puntaje:", salida["puntaje"])
    print("hallazgos:", salida["hallazgos"])
    print("habilidades detectadas:", salida["perfil"]["habilidades"])
    print(f"tiempo de ejecucion del grafo: {ms:.1f} ms")
