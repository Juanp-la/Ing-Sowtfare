"""NF03 - No inventar experiencia: el validador compara la salida del Extractor contra la HV original."""
import copy

import pytest

from core.datos_demo import PERFIL_DEMO
from core.models import EjecucionAgente, PerfilExtraido

from .utilidades import subir_y_analizar

pytestmark = pytest.mark.django_db


def test_ca1_dato_inventado_por_el_llm_es_rechazado(cliente_autenticado, llm_falso):
    inventado = copy.deepcopy(PERFIL_DEMO)
    inventado["experiencia"].append({"cargo": "Director de tecnología", "empresa": "Corporación Inexistente",
                                     "periodo": "2010 - 2020", "descripcion": "Lideró 200 personas"})
    inventado["habilidades"].append("Kubernetes")
    llm_falso.respuestas["PerfilHV"] = inventado

    hv, respuesta = subir_y_analizar(cliente_autenticado)

    datos = PerfilExtraido.objects.get(hoja_vida=hv).datos
    assert all(e["empresa"] != "Corporación Inexistente" for e in datos["experiencia"])
    assert "Kubernetes" not in datos["habilidades"] and "SQL" in datos["habilidades"]
    assert "descartó 5 dato(s)" in respuesta.content.decode()
    traza = EjecucionAgente.objects.get(agente="validador_extractor", hoja_vida=hv)
    assert "validacion{3}" in traza.salida_resumen


def test_ca2_sin_datos_inventados_el_perfil_pasa_completo(cliente_autenticado):
    hv, respuesta = subir_y_analizar(cliente_autenticado)
    datos = PerfilExtraido.objects.get(hoja_vida=hv).datos
    assert len(datos["experiencia"]) == 2 and "descartó" not in respuesta.content.decode()
    agentes = list(EjecucionAgente.objects.filter(hoja_vida=hv).order_by("id").values_list("agente", flat=True))
    assert agentes == ["supervisor", "extractor", "validador_extractor"]
