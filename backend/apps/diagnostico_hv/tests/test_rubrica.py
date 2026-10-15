"""Rúbrica configurable y determinista."""
import pytest
from django.core.exceptions import ImproperlyConfigured

from apps.diagnostico_hv.rubrica import CRITERIOS_POR_DEFECTO, Rubrica, nivel_para
from core.datos_demo import PERFIL_DEMO


def test_es_determinista():
    assert Rubrica().evaluar(PERFIL_DEMO) == Rubrica().evaluar(PERFIL_DEMO)


def test_pesos_configurables_por_settings(settings):
    settings.RUBRICA_PESOS = {"contacto": 5, "logros": 20}
    rubrica = Rubrica()
    assert {c.clave: c.peso for c in rubrica.criterios}["logros"] == 20
    assert Rubrica().evaluar(PERFIL_DEMO)["puntaje"] == 76
    settings.RUBRICA_PESOS = {"contacto": 50}
    with pytest.raises(ImproperlyConfigured):
        Rubrica()


def test_umbrales_de_nivel():
    assert [nivel_para(p) for p in (0, 49, 50, 74, 75, 100)] == ["bajo", "bajo", "por_mejorar", "por_mejorar",
                                                                  "competitivo", "competitivo"]


def test_perfil_vacio_da_cero_con_hallazgos_de_alta_prioridad():
    resultado = Rubrica().evaluar({})
    assert resultado["puntaje"] == 0 and resultado["nivel"] == "bajo"
    assert resultado["hallazgos"][0]["prioridad"] == "alta"


def test_casos_intermedios_de_los_criterios():
    perfil = {"contacto": {"nombre": "A", "email": "a@b.co", "telefono": "3000000", "ciudad": ""},
              "resumen": "x" * 700, "educacion": [{"titulo": "Técnico", "institucion": "Inst", "anio": ""}],
              "idiomas": ["Inglés B2"], "habilidades": [f"h{i}" for i in range(9)]}
    detalle = {c["clave"]: c for c in Rubrica().evaluar(perfil)["criterios"]}
    assert detalle["contacto"]["obtenido"] == 11.2 and detalle["resumen"]["obtenido"] == 5
    assert detalle["educacion"]["obtenido"] == 15 and detalle["idiomas"]["obtenido"] == 10
    assert detalle["habilidades"]["obtenido"] == 15 and detalle["logros"]["obtenido"] == 0
    assert len(CRITERIOS_POR_DEFECTO) == 7
