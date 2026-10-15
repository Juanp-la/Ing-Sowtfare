"""HU10 - Requisitos que cumplo y no cumplo (criterios derivados, no oficiales)."""
import pytest

from core.models import Vacante

pytestmark = pytest.mark.django_db


def _detalle(cliente, magneto_id):
    vacante = Vacante.objects.get(magneto_id=magneto_id)
    return cliente.get(f"/vacantes/{vacante.pk}/").content.decode()


def test_ca1_detalle_requisito_por_requisito_con_evidencia(cliente_autenticado, hv_demo, vacantes_demo):
    html = _detalle(cliente_autenticado, "MAG-V-003")  # Analista de datos junior
    cumple = html.split('id="requisitos-cumple"')[1].split('id="requisitos-no-cumple"')[0]
    no_cumple = html.split('id="requisitos-no-cumple"')[1]
    assert "SQL" in cumple and "Habilidad declarada: SQL" in cumple
    for faltante in ("Python", "Power BI", "profesional", "Inglés B2"):
        assert faltante in no_cumple
    assert "No aparece en la hoja de vida" in no_cumple and "Nivel en la HV: tecnólogo" in no_cumple


def test_ca2_resumen_y_marcas_de_obligatorio(cliente_autenticado, hv_demo, vacantes_demo):
    html = _detalle(cliente_autenticado, "MAG-V-003")
    assert 'id="resumen-requisitos">Cumples 1 de 5 requisitos.' in html
    assert html.count("Obligatorio") == 3 and 'id="ajuste-total"' in html


def test_ca3_cumple_todo(cliente_autenticado, hv_demo, vacantes_demo):
    html = _detalle(cliente_autenticado, "MAG-V-001")
    assert "¡Cumples todos los requisitos!" in html and "Cumples 5 de 5 requisitos." in html


def test_ca4_vacante_inexistente_o_cerrada_da_404(cliente_autenticado, hv_demo, vacantes_demo):
    cerrada = vacantes_demo[0]
    cerrada.activa = False
    cerrada.save()
    assert cliente_autenticado.get(f"/vacantes/{cerrada.pk}/").status_code == 404
    assert cliente_autenticado.get("/vacantes/999999/").status_code == 404


def test_ca5_sin_hv_invita_a_cargarla(cliente_autenticado, vacantes_demo):
    assert "Carga y analiza tu hoja de vida" in _detalle(cliente_autenticado, "MAG-V-001")


def test_detalle_sin_ajuste_calculado_muestra_error(cliente_autenticado, hv_demo, vacantes_demo, monkeypatch):
    from apps.matching_vacantes import servicios

    monkeypatch.setattr(servicios, "calcular_ajustes", lambda *a, **k: False)
    assert "No fue posible calcular el ajuste" in _detalle(cliente_autenticado, "MAG-V-002")
