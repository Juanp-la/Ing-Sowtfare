"""NF01 - Diagnóstico en menos de 30 s (criterio oficial, Entrega 1 §3.4)."""
from datetime import timedelta

import pytest

from apps.diagnostico_hv import servicios
from core.llm.mock import MockLLMClient
from core.models import Diagnostico, EjecucionAgente
from core.pruebas.fabricas import crear_hv

pytestmark = pytest.mark.django_db


def test_ca1_se_mide_el_tiempo_por_nodo_con_latencia_simulada(cliente_autenticado, hv_demo, diagnosticar, llm_falso):
    llm_falso.latencia_s = 0.3
    diagnostico = diagnosticar(hv_demo)
    evaluador = EjecucionAgente.objects.get(ejecucion_id=diagnostico.ejecucion_id, agente="evaluador")
    assert evaluador.duracion_ms >= 300 and diagnostico.duracion_ms >= 300
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert "evaluador:" in html and "Tiempo total:" in html


def test_ca1_diez_diagnosticos_en_menos_de_30_s_el_90_por_ciento(usuario, diagnosticar):
    duraciones = sorted(diagnosticar(crear_hv(usuario)).duracion_ms for _ in range(10))
    assert duraciones[8] < 30_000  # percentil 90


def test_ca2_indicador_de_progreso_sin_bloquear_la_interfaz(cliente_autenticado, hv_demo, settings, monkeypatch):
    pendientes = []
    settings.COPILOTO_TAREAS_ASINCRONAS = True
    monkeypatch.setattr(servicios.tareas, "lanzar", lambda funcion, *args: pendientes.append((funcion, args)))

    respuesta = cliente_autenticado.post(f"/diagnostico/hv/{hv_demo.pk}/diagnosticar/", follow=True)
    diagnostico = Diagnostico.objects.get()
    html = respuesta.content.decode()
    assert respuesta.status_code == 200 and 'id="progreso"' in html and 'role="progressbar"' in html
    estado = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/estado.json").json()
    assert estado["terminado"] is False and estado["lento"] is False

    funcion, args = pendientes.pop()
    funcion(*args)
    estado = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/estado.json").json()
    assert estado["terminado"] is True and estado["puntaje"] == 86 and estado["nodos"] == ["supervisor", "evaluador"]


def test_ca2_si_supera_30_s_avisa_que_sigue_trabajando(cliente_autenticado, hv_demo):
    diagnostico = Diagnostico.objects.create(hoja_vida=hv_demo)
    Diagnostico.objects.filter(pk=diagnostico.pk).update(fecha=diagnostico.fecha - timedelta(seconds=31))
    assert cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/estado.json").json()["lento"] is True
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert 'id="progreso-lento"' in html and "d-none" not in html.split('id="progreso-lento"')[0][-120:]


def test_cache_del_llm_acelera_diagnosticos_repetidos(hv_demo, diagnosticar, settings):
    from core.llm import fabrica
    from core.llm.cache import LLMConCache

    fabrica.establecer_llm(LLMConCache(MockLLMClient(latencia_s=0.3)))
    primero = diagnosticar(hv_demo)
    segundo = diagnosticar(hv_demo)
    assert primero.duracion_ms >= 300 and segundo.duracion_ms < 300


def test_errores_del_grafo_y_de_cuota_quedan_en_el_diagnostico(hv_demo):
    class Falla:
        def ejecutar(self, *a, **k):
            return {"error": "evaluador: ValueError"}

    class SinCuota:
        def ejecutar(self, *a, **k):
            from core.servicios.cuota import CuotaAgotada

            raise CuotaAgotada()

    for servicio, texto in ((Falla(), "no pudo completarse"), (SinCuota(), "cuota mensual")):
        diagnostico = Diagnostico.objects.create(hoja_vida=hv_demo, ejecucion_id="x")
        resultado = servicios.ejecutar_diagnostico(diagnostico.pk, servicio=servicio)
        assert resultado.estado == Diagnostico.Estado.ERROR and texto in resultado.mensaje_error
    assert servicios.tiempos_por_nodo(Diagnostico(hoja_vida=hv_demo)) == []


def test_sin_cuota_no_se_inicia_el_diagnostico(cliente_autenticado, usuario, hv_demo):
    usuario.cuota_tokens_mes = 0
    usuario.save()
    respuesta = cliente_autenticado.post(f"/diagnostico/hv/{hv_demo.pk}/diagnosticar/")
    assert respuesta.status_code == 429 and not Diagnostico.objects.exists()
