"""HU07 - Explicación del puntaje (criterios derivados, no oficiales)."""
import pytest

pytestmark = pytest.mark.django_db


def test_ca1_cada_criterio_muestra_peso_puntos_y_evidencia(cliente_autenticado, hv_demo, diagnosticar):
    diagnostico = diagnosticar(hv_demo)
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert len(diagnostico.criterios) == 7 and sum(c["peso"] for c in diagnostico.criterios) == 100
    assert html.count('class="criterio"') == 7
    habilidades = next(c for c in diagnostico.criterios if c["clave"] == "habilidades")
    assert habilidades["peso"] == 15 and habilidades["obtenido"] == 11.2
    assert "6 habilidad(es): SQL" in habilidades["evidencia"] and "6 habilidad(es): SQL" in html


def test_ca2_la_suma_de_lo_obtenido_explica_el_puntaje(hv_demo, diagnosticar):
    diagnostico = diagnosticar(hv_demo)
    assert round(sum(c["obtenido"] for c in diagnostico.criterios)) == diagnostico.puntaje


def test_ca3_resumen_en_lenguaje_natural_generado_por_el_agente(cliente_autenticado, hv_demo, diagnosticar, llm_falso):
    diagnostico = diagnosticar(hv_demo)
    assert diagnostico.explicacion.startswith("Tu hoja de vida obtiene 86/100 (nivel competitivo).")
    assert "Puedes ganar puntos en: logros medibles, habilidades." in diagnostico.explicacion
    assert llm_falso.llamadas[0]["esquema"] == "ExplicacionDiagnostico"


def test_ca4_el_llm_no_puede_cambiar_el_puntaje(hv_demo, diagnosticar, llm_falso):
    llm_falso.respuestas["ExplicacionDiagnostico"] = {"resumen": "Texto del modelo"}
    diagnostico = diagnosticar(hv_demo)
    assert diagnostico.puntaje == 86 and diagnostico.explicacion == "Texto del modelo"
