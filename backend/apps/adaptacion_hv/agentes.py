"""Nodos de la Feature 5: agente Redactor y su validador de veracidad (NF03).

Intención "adaptar_hv": supervisor -> redactor -> validador_redactor -> END

El Redactor no escribe una HV nueva: propone cambios puntuales (reordenar, resaltar, palabras clave)
usando solo lo que ya está en la HV. Cada cambio guarda el original y la propuesta para que el candidato
los compare (HU13) y decida (HU14). El validador descarta cualquier cambio que meta requisitos de la
vacante o cifras que no aparezcan en la HV.
"""
from pydantic import BaseModel, Field

from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo
from core.agentes.validador import ValidadorVeracidad
from core.dominio.requisitos import evaluar_requisitos
from core.dominio.texto import normalizar, palabras

PROMPT_REDACTOR = (
    "Eres el agente Redactor de Magneto Copiloto. Propón cambios puntuales a la hoja de vida para la vacante "
    "{titulo}: reordenar habilidades y experiencia por relevancia, resaltar lo que ya cumple y sugerir palabras "
    "clave. Usa solo información de la hoja de vida; nunca agregues habilidades, cargos, cifras ni requisitos "
    "de la vacante que el candidato no tenga.\nRequisitos que cumple: {cumple}\nHOJA DE VIDA:\n{texto}"
)

PALABRAS_GENERICAS = {"con", "para", "por", "los", "las", "del", "una", "uno", "que", "como", "sus", "nivel",
                      "experiencia", "conocimiento", "conocimientos", "manejo"}


class CambioPropuesto(BaseModel):
    id: str
    seccion: str
    titulo: str
    original: str | list[str] = ""
    propuesta: str | list[str] = ""
    motivo: str = ""


class AdaptacionHV(BaseModel):
    cambios: list[CambioPropuesto] = Field(default_factory=list)


def etiqueta_experiencia(exp):
    periodo = f" ({exp.get('periodo')})" if exp.get("periodo") else ""
    empresa = f" - {exp.get('empresa')}" if exp.get("empresa") else ""
    return f"{exp.get('cargo', '')}{empresa}{periodo}".strip()


def _terminos(texto):
    return {p for p in palabras(texto) if len(p) >= 3 and p not in PALABRAS_GENERICAS}


def relevancia(texto, requisitos):
    """Cuántos requisitos de la vacante se mencionan en el texto (palabra por palabra)."""
    terminos = _terminos(texto)
    return sum(1 for r in requisitos if _terminos(r.get("valor", "")) and _terminos(r.get("valor", "")) <= terminos)


def _ordenar_por_relevancia(items, requisitos, texto_de=str):
    con_indice = list(enumerate(items))
    con_indice.sort(key=lambda par: (-relevancia(texto_de(par[1]), requisitos), par[0]))  # estable
    return [item for _, item in con_indice]


def cambios_por_reglas(perfil, vacante):
    requisitos = vacante.get("requisitos", [])
    titulo = vacante.get("titulo", "la vacante")
    cumple, _ = evaluar_requisitos(perfil, requisitos)
    cambios = []

    habilidades = list(perfil.get("habilidades", []))
    relevantes = [h for h in habilidades if relevancia(h, requisitos)]
    ordenadas = _ordenar_por_relevancia(habilidades, requisitos)
    if ordenadas != habilidades:
        cambios.append({
            "id": "habilidades", "seccion": "habilidades", "titulo": "Orden de las habilidades",
            "original": habilidades, "propuesta": ordenadas,
            "motivo": f"Primero las habilidades que pide la vacante ({', '.join(relevantes)}).",
        })

    experiencia = list(perfil.get("experiencia", []))
    etiquetas = [etiqueta_experiencia(e) for e in experiencia]
    ordenada = _ordenar_por_relevancia(
        experiencia, requisitos, texto_de=lambda e: f"{e.get('cargo', '')} {e.get('descripcion', '')}")
    if [etiqueta_experiencia(e) for e in ordenada] != etiquetas:
        cambios.append({
            "id": "experiencia", "seccion": "experiencia", "titulo": "Orden de la experiencia",
            "original": etiquetas, "propuesta": [etiqueta_experiencia(e) for e in ordenada],
            "motivo": "Primero la experiencia más relacionada con la vacante.",
        })

    resumen = (perfil.get("resumen") or "").strip()
    destacadas = [h for h in relevantes if normalizar(h) not in normalizar(resumen)][:4]  # sin repetir lo dicho
    if destacadas:
        frase = f"Dominio de {', '.join(destacadas[:-1]) + ' y ' + destacadas[-1] if len(destacadas) > 1 else destacadas[0]}."
        propuesta = f"{resumen} {frase}".strip() if resumen else frase
        if normalizar(frase) not in normalizar(resumen):
            cambios.append({
                "id": "resumen", "seccion": "resumen", "titulo": "Resumen profesional",
                "original": resumen, "propuesta": propuesta,
                "motivo": f"El resumen nombra lo que pide la vacante {titulo} y ya está en tu HV.",
            })

    clave = [r["requisito"] for r in cumple if r["tipo"] in ("habilidad", "idioma")]
    if clave:
        cambios.append({
            "id": "palabras_clave", "seccion": "palabras_clave", "titulo": "Palabras clave para la vacante",
            "original": list(perfil.get("palabras_clave", [])), "propuesta": clave,
            "motivo": "Los filtros de los reclutadores buscan estos términos tal como aparecen en la vacante.",
        })
    return cambios


class AgenteRedactor(AgenteBase):
    nombre = "redactor"

    def ejecutar(self, estado):
        perfil = estado.get("perfil") or {}
        vacante = estado.get("vacante") or {}
        cumple, _ = evaluar_requisitos(perfil, vacante.get("requisitos", []))
        borrador = {"cambios": cambios_por_reglas(perfil, vacante)}
        prompt = PROMPT_REDACTOR.format(titulo=vacante.get("titulo", ""), cumple=[r["requisito"] for r in cumple],
                                        texto=estado.get("texto_hv", ""))
        resultado = self.consultar_llm(prompt, AdaptacionHV, borrador=borrador)
        return {"datos": {**estado.get("datos", {}), "adaptacion": [c.model_dump() for c in resultado.cambios]}}


class ValidadorRedactor(AgenteBase):
    """NF03 aplicado a la adaptación: nada que no esté en la HV original entra a la propuesta.

    - Listas (habilidades, palabras clave, experiencia): cada elemento debe estar soportado por la HV.
    - Textos (resumen): no puede aparecer ningún término de la vacante ni ninguna cifra que no esté en la HV.
    """

    nombre = "validador_redactor"

    def __init__(self, llm=None, trazador=None, validador=None):
        super().__init__(llm=llm, trazador=trazador)
        self.validador = validador or ValidadorVeracidad()

    def ejecutar(self, estado):
        original = estado.get("texto_hv", "")
        vacante = estado.get("vacante") or {}
        datos = dict(estado.get("datos", {}))
        contexto = (normalizar(original), set(palabras(original)))
        terminos_vacante = _terminos(vacante.get("titulo", "") + " " + " ".join(
            r.get("valor", "") for r in vacante.get("requisitos", [])))
        aceptados, rechazados = [], []
        for cambio in datos.get("adaptacion", []):
            propuesta = cambio.get("propuesta")
            if isinstance(propuesta, list):
                limpios = [p for p in propuesta if self.validador.soportado(p, *contexto)]
                rechazados += [p for p in propuesta if p not in limpios]
                cambio = {**cambio, "propuesta": limpios}
                if limpios and limpios != cambio.get("original"):
                    aceptados.append(cambio)
                continue
            nuevos = set(palabras(propuesta)) - set(palabras(cambio.get("original", "")))
            inventados = sorted(t for t in nuevos if (t in terminos_vacante or t.isdigit()) and t not in contexto[1])
            if inventados:
                rechazados += inventados
            elif propuesta and propuesta != cambio.get("original"):
                aceptados.append(cambio)
        datos["adaptacion"] = aceptados
        return {"datos": datos, "validacion": {"ok": not rechazados, "rechazados": rechazados, "campo": "adaptacion"}}


registrar_nodo("redactor", AgenteRedactor, intenciones=["adaptar_hv"], orden=20)
registrar_nodo("validador_redactor", ValidadorRedactor, intenciones=["adaptar_hv"], orden=25)
