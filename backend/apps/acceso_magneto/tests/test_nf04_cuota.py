"""NF04 - Límite de consumo LLM por usuario (criterios derivados, no oficiales)."""
import pytest
from django.test import override_settings

from core.agentes.base import AgenteBase
from core.models import EjecucionAgente
from core.servicios.cuota import ControlCuota

pytestmark = pytest.mark.django_db


class AgenteCostoso(AgenteBase):
    nombre = "costoso"

    def ejecutar(self, estado):
        self._tokens += 400
        return {"explicacion": "ok"}


@pytest.fixture
def nodo_de_prueba(registro_aislado):
    registro_aislado.registrar_nodo("costoso", AgenteCostoso, intenciones=["prueba_cuota"])


def test_ca1_el_panel_muestra_el_consumo_del_mes(cliente_autenticado, usuario):
    usuario.cuota_tokens_mes = 1000
    usuario.save()
    ControlCuota().registrar_consumo(usuario, 250, agente="extractor")
    html = cliente_autenticado.get("/magneto/consumo/").content.decode()
    assert 'id="tokens-usados">250<' in html and "de 1000 tokens" in html and "extractor" in html
    assert 'aria-valuenow="25"' in html


def test_ca1_indicador_de_cuota_visible_en_la_barra(cliente_autenticado):
    assert 'id="indicador-cuota"' in cliente_autenticado.get("/").content.decode()


def test_ca1_estado_vacio_sin_consumo(cliente_autenticado):
    assert "Aún no has usado los agentes este mes." in cliente_autenticado.get("/magneto/consumo/").content.decode()


@override_settings(ROOT_URLCONF="apps.acceso_magneto.tests.urls_prueba")
def test_ca2_la_cuota_se_verifica_antes_de_invocar_el_grafo(cliente_autenticado, usuario, nodo_de_prueba):
    usuario.cuota_tokens_mes = 500
    usuario.save()
    assert cliente_autenticado.get("/prueba/grafo/").content == b"grafo invocado"
    assert ControlCuota().consumo_mes(usuario) == 400


@override_settings(ROOT_URLCONF="apps.acceso_magneto.tests.urls_prueba")
def test_ca3_al_agotarse_la_cuota_se_bloquean_los_agentes(cliente_autenticado, usuario, nodo_de_prueba):
    usuario.cuota_tokens_mes = 300
    usuario.save()
    ControlCuota().registrar_consumo(usuario, 300)
    respuesta = cliente_autenticado.get("/prueba/grafo/")
    assert respuesta.status_code == 429 and "Cuota de uso agotada" in respuesta.content.decode()
    assert not EjecucionAgente.objects.filter(agente="costoso").exists()
    panel = cliente_autenticado.get("/magneto/consumo/").content.decode()
    assert 'id="cuota-bloqueada"' in panel and "agotada" in cliente_autenticado.get("/").content.decode()


def test_consumo_requiere_sesion(client):
    assert client.get("/magneto/consumo/").status_code == 302
