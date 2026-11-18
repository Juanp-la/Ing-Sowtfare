"""HU14 - Aprobar o rechazar los cambios antes de aplicarlos (criterios derivados, por validar con el PO)."""
import pytest
from docx import Document

from core.datos_demo import PERFIL_DEMO
from core.models import HVAdaptada, PerfilExtraido

pytestmark = pytest.mark.django_db


def _decidir(cliente, adaptacion, **decisiones):
    datos = {f"decision_{k}": v for k, v in decisiones.items()}
    return cliente.post(f"/adaptacion/{adaptacion.pk}/", datos, follow=True)


def test_ca1_cada_cambio_tiene_aprobar_y_rechazar(cliente_autenticado, adaptacion):
    html = cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/").content.decode()
    for cambio in adaptacion.cambios:
        assert f'id="aprobar_{cambio["id"]}"' in html and f'id="rechazar_{cambio["id"]}"' in html


def test_ca2_solo_se_aplican_los_cambios_aprobados(cliente_autenticado, adaptacion):
    decisiones = {c["id"]: "rechazar" for c in adaptacion.cambios}
    decisiones["habilidades"] = "aprobar"
    _decidir(cliente_autenticado, adaptacion, **decisiones)
    adaptacion.refresh_from_db()
    assert adaptacion.estado == HVAdaptada.Estado.APLICADA
    assert adaptacion.perfil_adaptado["habilidades"][:2] == ["SQL", "Zendesk"]
    assert adaptacion.perfil_adaptado["resumen"] == PERFIL_DEMO["resumen"]
    assert "palabras_clave" not in adaptacion.perfil_adaptado


def test_ca3_la_hv_original_nunca_se_modifica(cliente_autenticado, adaptacion, hv_demo):
    _decidir(cliente_autenticado, adaptacion, **{c["id"]: "aprobar" for c in adaptacion.cambios})
    assert PerfilExtraido.objects.get(hoja_vida=hv_demo).datos == PERFIL_DEMO


def test_ca4_sin_decidir_todos_no_se_aplica_nada(cliente_autenticado, adaptacion):
    html = _decidir(cliente_autenticado, adaptacion, habilidades="aprobar").content.decode()
    adaptacion.refresh_from_db()
    assert adaptacion.estado == HVAdaptada.Estado.PENDIENTE and "Falta decidir" in html


def test_ca5_rechazar_todo_descarta_la_adaptacion(cliente_autenticado, adaptacion):
    html = _decidir(cliente_autenticado, adaptacion, **{c["id"]: "rechazar" for c in adaptacion.cambios}).content.decode()
    adaptacion.refresh_from_db()
    assert adaptacion.estado == HVAdaptada.Estado.DESCARTADA and "Rechazaste todos los cambios" in html


def test_ca6_una_vez_decidida_no_se_vuelve_a_decidir(cliente_autenticado, adaptacion):
    _decidir(cliente_autenticado, adaptacion, **{c["id"]: "aprobar" for c in adaptacion.cambios})
    html = _decidir(cliente_autenticado, adaptacion, **{c["id"]: "rechazar" for c in adaptacion.cambios}).content.decode()
    adaptacion.refresh_from_db()
    assert adaptacion.estado == HVAdaptada.Estado.APLICADA and "ya fue decidida" in html
    assert 'id="btn-aplicar"' not in html and 'class="badge decision text-bg-success"' in html


def test_la_version_aplicada_se_descarga_en_word(cliente_autenticado, adaptacion, tmp_path):
    assert cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/descargar/").status_code == 404
    _decidir(cliente_autenticado, adaptacion, **{c["id"]: "aprobar" for c in adaptacion.cambios})
    respuesta = cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/descargar/")
    ruta = tmp_path / "hv.docx"
    ruta.write_bytes(respuesta.content)
    texto = "\n".join(p.text for p in Document(ruta).paragraphs)
    assert "Dominio de SQL y Zendesk." in texto and "Palabras clave" in texto and "Ana Demo Restrepo" in texto


def test_aplicar_experiencia_reordena_el_perfil():
    from apps.adaptacion_hv.servicios import aplicar_cambio

    perfil = {"experiencia": [{"cargo": "A", "empresa": "X", "periodo": "2020"}, {"cargo": "B"}]}
    resultado = aplicar_cambio(perfil, {"seccion": "experiencia", "propuesta": ["B"]})
    assert [e["cargo"] for e in resultado["experiencia"]] == ["B", "A"]


def test_eliminar_adaptacion_desde_la_lista(cliente_autenticado, adaptacion):
    html = cliente_autenticado.get("/adaptacion/").content.decode()
    assert 'id="tabla-adaptaciones"' in html and f"/adaptacion/{adaptacion.pk}/eliminar/" in html
    assert "Sí, eliminar" in cliente_autenticado.get(f"/adaptacion/{adaptacion.pk}/eliminar/").content.decode()
    cliente_autenticado.post(f"/adaptacion/{adaptacion.pk}/eliminar/")
    assert not HVAdaptada.objects.filter(pk=adaptacion.pk).exists()
