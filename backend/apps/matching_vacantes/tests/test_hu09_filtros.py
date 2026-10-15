"""HU09 - Filtrar vacantes por ciudad, modalidad y salario (criterios derivados, no oficiales)."""
import pytest

from core.models import Vacante

from .test_hu08_ranking import _orden

pytestmark = pytest.mark.django_db


def _vacantes(cliente, **filtros):
    html = cliente.get("/vacantes/", filtros).content.decode()
    return [Vacante.objects.get(magneto_id=m) for m in _orden(html)], html


def test_ca1_filtra_por_ciudad(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, html = _vacantes(cliente_autenticado, ciudad="Cali")
    assert vacantes and {v.ciudad for v in vacantes} == {"Cali"}
    assert '<option value="Cali" selected>' in html


def test_ca2_filtra_por_modalidad(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, _ = _vacantes(cliente_autenticado, modalidad="remoto")
    assert len(vacantes) == Vacante.objects.filter(modalidad="remoto").count() == 3
    assert all(v.modalidad == "remoto" for v in vacantes)


def test_ca3_filtra_por_rango_salarial(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, _ = _vacantes(cliente_autenticado, salario_min=3000000, salario_max=4000000)
    assert vacantes and all(v.salario_max >= 3000000 and v.salario_min <= 4000000 for v in vacantes)
    assert "MAG-V-004" not in [v.magneto_id for v in vacantes]  # 5-7 millones queda fuera


def test_ca4_filtros_combinados_mantienen_el_orden_por_ajuste(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, _ = _vacantes(cliente_autenticado, ciudad="Medellín", modalidad="presencial")
    assert {v.magneto_id for v in vacantes} == {"MAG-V-007", "MAG-V-010"}
    puntajes = [v.ajustes.get(perfil=hv_demo.perfil).score for v in vacantes]
    assert puntajes == sorted(puntajes, reverse=True)


def test_ca5_sin_resultados_muestra_mensaje(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, html = _vacantes(cliente_autenticado, ciudad="Cali", modalidad="remoto")
    assert vacantes == [] and "No hay vacantes con esos filtros." in html


def test_ca6_rango_salarial_invertido_muestra_error_y_no_filtra(cliente_autenticado, hv_demo, vacantes_demo):
    vacantes, html = _vacantes(cliente_autenticado, salario_min=5000000, salario_max=1000000)
    assert 'id="error-filtros"' in html and len(vacantes) == 12


def test_rango_salarial_del_catalogo(vacantes_demo):
    from apps.matching_vacantes.servicios import rango_salarial

    assert rango_salarial() == {"minimo": 1300000, "maximo": 7000000}
