"""Nodos de la Feature 2 en el grafo: Extractor y su validador de veracidad (NF03).

Intención "extraer_perfil": supervisor -> extractor -> validador_extractor -> END
"""
from core.agentes.base import AgenteBase
from core.agentes.registro import registrar_nodo
from core.agentes.validador import NodoValidador
from core.llm.esquemas import PerfilHV

from .parser_hv import parsear_hv

PROMPT_EXTRACTOR = (
    "Eres el agente Extractor de Magneto Copiloto. Convierte la hoja de vida en el esquema PerfilHV. "
    "Usa solo información que aparezca en el texto; si un dato no está, déjalo vacío. "
    "No inventes cargos, empresas, fechas, títulos ni habilidades.\n\nHOJA DE VIDA:\n{texto}"
)


class AgenteExtractor(AgenteBase):
    nombre = "extractor"

    def ejecutar(self, estado):
        texto = estado.get("texto_hv", "")
        borrador = parsear_hv(texto)
        perfil = self.consultar_llm(PROMPT_EXTRACTOR.format(texto=texto), PerfilHV, borrador=borrador)
        return {"perfil": perfil.model_dump()}


class ValidadorExtractor(NodoValidador):
    """NF03: el Extractor no puede devolver datos que no estén en el texto fuente."""

    nombre = "validador_extractor"
    campo = "perfil"
    campo_original = "texto_hv"


registrar_nodo("extractor", AgenteExtractor, intenciones=["extraer_perfil"], orden=10)
registrar_nodo("validador_extractor", ValidadorExtractor, intenciones=["extraer_perfil"], orden=15)
