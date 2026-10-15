from datetime import timedelta

import pytest
from django.utils import timezone

from core.agentes.base import AgenteBase
from core.models import EjecucionAgente
from core.servicios import tareas
from core.servicios.copiloto import CopilotoService, IntencionNoDisponible
from core.servicios.cuota import ControlCuota, CuotaAgotada

pytestmark = pytest.mark.django_db


class AgenteGasta(AgenteBase):
    nombre = "gasta"

    def ejecutar(self, estado):
        self._tokens += 50
        return {"explicacion": "listo"}


@pytest.fixture
def con_nodo(registro_aislado):
    registro_aislado.registrar_nodo("gasta", AgenteGasta, intenciones=["gastar"])
    return registro_aislado


def test_consumo_del_mes_ignora_meses_anteriores(usuario):
    control = ControlCuota()
    EjecucionAgente.objects.create(usuario=usuario, agente="x", tokens=300)
    EjecucionAgente.objects.create(usuario=usuario, agente="x", tokens=999,
                                   fecha=control.inicio_mes() - timedelta(days=1))
    assert control.consumo_mes(usuario) == 300
    usuario.cuota_tokens_mes = 1000
    assert control.disponible(usuario) == 700 and control.porcentaje_usado(usuario) == 30
    assert control.resumen(usuario) == {"cuota": 1000, "consumo": 300, "disponible": 700,
                                        "porcentaje": 30, "agotada": False}


def test_cuota_agotada_y_cuota_cero(usuario):
    control = ControlCuota()
    usuario.cuota_tokens_mes = 100
    control.registrar_consumo(usuario, 100)
    assert not control.verificar(usuario) and control.resumen(usuario)["agotada"]
    usuario.cuota_tokens_mes = 0
    assert control.porcentaje_usado(usuario) == 100


def test_fachada_ejecuta_el_grafo_y_registra_consumo(usuario, con_nodo):
    resultado = CopilotoService().ejecutar(usuario, "gastar", texto_hv="x")
    assert resultado["explicacion"] == "listo" and resultado["tokens_usados"] == 50
    assert ControlCuota().consumo_mes(usuario) == 50


def test_fachada_verifica_cuota_antes_de_invocar(usuario, con_nodo):
    usuario.cuota_tokens_mes = 10
    usuario.save()
    ControlCuota().registrar_consumo(usuario, 10)
    with pytest.raises(CuotaAgotada):
        CopilotoService().ejecutar(usuario, "gastar")
    assert not EjecucionAgente.objects.filter(agente="gasta").exists()


def test_fachada_detecta_cuota_agotada_dentro_del_grafo(usuario, con_nodo):
    class ControlQueCambia(ControlCuota):
        llamadas = 0

        def verificar(self, u):
            ControlQueCambia.llamadas += 1
            return ControlQueCambia.llamadas == 1

    with pytest.raises(CuotaAgotada):
        CopilotoService(control_cuota=ControlQueCambia()).ejecutar(usuario, "gastar")


def test_fachada_rechaza_intencion_sin_nodos(usuario):
    with pytest.raises(IntencionNoDisponible):
        CopilotoService().ejecutar(usuario, "intencion_inexistente")


def test_tareas_en_linea_y_en_segundo_plano(settings):
    resultados = []
    settings.COPILOTO_TAREAS_ASINCRONAS = False
    assert tareas.lanzar(resultados.append, 1) is None
    settings.COPILOTO_TAREAS_ASINCRONAS = True
    hilo = tareas.lanzar(resultados.append, 2)
    hilo.join(timeout=5)
    assert resultados == [1, 2]

    def fallar():
        raise RuntimeError("x")

    tareas.lanzar(fallar).join(timeout=5)  # el error se registra y no se propaga


def test_inicio_de_mes_usa_hora_local():
    ahora = timezone.now()
    assert ControlCuota().inicio_mes(ahora).day == 1
