"""HU13 - Ver lado a lado la versión original y la adaptada (criterios derivados, por validar con el PO)."""
import pytest

from apps.adaptacion_hv import servicios
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


def test_ca1_cada_cambio_muestra_original_y_adaptada_en_dos_columnas(cliente_autenticado, adaptacion):
    html = cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/").content.decode()
    assert html.count('class="col-12 col-md-6 columna-original"') == len(adaptacion.cambios)
    assert html.count('class="col-12 col-md-6 columna-adaptada"') == len(adaptacion.cambios)
    assert "col-md-6" in html  # en el celular las columnas se apilan (NF06)


def test_ca2_lo_que_cambia_se_resalta(cliente_autenticado, adaptacion):
    html = cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/").content.decode()
    assert '<mark class="nuevo">Dominio de SQL y Zendesk.</mark>' in html
    assert 'class="fw-semibold movido">Zendesk</span>' in html


def test_ca3_cada_cambio_explica_el_motivo(cliente_autenticado, adaptacion):
    html = cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/").content.decode()
    assert all(c["motivo"] in html for c in adaptacion.cambios)


def test_ca4_solo_el_dueno_ve_la_comparacion(client, adaptacion):
    client.force_login(crear_usuario())
    assert client.get(f"/adaptacion/{adaptacion.pk}/").status_code == 404


def test_comparacion_marca_elementos_nuevos_en_listas():
    class Falsa:
        cambios = [{"id": "x", "seccion": "palabras_clave", "titulo": "t", "original": ["A"], "propuesta": ["B", "A"],
                    "motivo": "m"}]

    fila = servicios.comparacion(Falsa())[0]
    assert fila["propuesta_items"][0]["nuevo"] and fila["propuesta_items"][1]["movido"]
