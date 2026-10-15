"""NF05 - Trazabilidad por agente (criterios derivados, no oficiales)."""
import pytest

from core.models import EjecucionAgente
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


def test_ca1_cada_ejecucion_registra_agente_tokens_y_duracion(hv_demo, diagnosticar):
    diagnostico = diagnosticar(hv_demo)
    filas = EjecucionAgente.objects.filter(ejecucion_id=diagnostico.ejecucion_id).order_by("id")
    assert [f.agente for f in filas] == ["supervisor", "evaluador"]
    evaluador = filas[1]
    assert evaluador.tokens > 0 and evaluador.duracion_ms >= 0 and evaluador.estado == "ok"
    assert evaluador.hoja_vida_id == hv_demo.pk and len(evaluador.entrada_hash) == 64
    assert "puntaje=86" in evaluador.salida_resumen and "ana.demo" not in evaluador.salida_resumen


def test_ca2_la_vista_muestra_la_trazabilidad_y_filtra_por_agente(cliente_autenticado, hv_demo, diagnosticar):
    diagnosticar(hv_demo)
    html = cliente_autenticado.get("/diagnostico/trazabilidad/").content.decode()
    assert 'id="tabla-trazas"' in html and "evaluador" in html and "supervisor" in html
    filtrado = cliente_autenticado.get("/diagnostico/trazabilidad/?agente=evaluador").content.decode()
    tabla = filtrado.split('id="tabla-trazas"')[1]
    assert "evaluador" in tabla and ">supervisor<" not in tabla


def test_ca3_cada_usuario_solo_ve_sus_trazas_y_el_admin_ve_todas(client, hv_demo, diagnosticar):
    diagnosticar(hv_demo)
    client.force_login(crear_usuario())
    assert "Aún no hay ejecuciones de agentes registradas." in client.get("/diagnostico/trazabilidad/").content.decode()
    client.force_login(crear_usuario(is_staff=True))
    assert "evaluador" in client.get("/diagnostico/trazabilidad/").content.decode()
