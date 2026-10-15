"""HU05 - Puntaje de la HV. Criterios oficiales (Entrega 1 §3.4)."""
import copy

import pytest

from core.datos_demo import PERFIL_DEMO
from core.models import Diagnostico, HojaVida
from core.pruebas.fabricas import crear_hv

pytestmark = pytest.mark.django_db


def test_ca1_puntaje_entre_0_y_100_con_nivel(cliente_autenticado, hv_demo, diagnosticar):
    diagnostico = diagnosticar(hv_demo)
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert diagnostico.estado == Diagnostico.Estado.COMPLETADO
    assert 0 <= diagnostico.puntaje <= 100 and diagnostico.puntaje == 86
    assert diagnostico.nivel == "competitivo"
    assert 'id="puntaje">86<' in html and 'id="nivel">Competitivo<' in html


def test_ca1_niveles_bajo_y_por_mejorar(usuario, diagnosticar, perfil_debil):
    bajo = diagnosticar(crear_hv(usuario, perfil=perfil_debil))
    assert bajo.nivel == "bajo" and bajo.puntaje < 50
    medio = copy.deepcopy(PERFIL_DEMO)
    medio["resumen"] = ""
    medio["habilidades"] = ["Excel"]
    por_mejorar = diagnosticar(crear_hv(usuario, perfil=medio))
    assert por_mejorar.nivel == "por_mejorar" and 50 <= por_mejorar.puntaje < 75


def test_ca2_hv_que_no_pudo_procesarse_muestra_mensaje_en_vez_de_puntaje(cliente_autenticado, usuario, diagnosticar):
    hv = crear_hv(usuario, texto="", perfil=None, estado=HojaVida.Estado.ERROR)
    diagnostico = diagnosticar(hv)
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert diagnostico.puntaje is None
    assert "No fue posible leer el archivo, intente con otro formato" in html and 'id="puntaje"' not in html


def test_ca2_perfil_ilegible_tambien_muestra_el_mensaje(usuario, diagnosticar):
    diagnostico = diagnosticar(crear_hv(usuario, perfil={}))
    assert diagnostico.estado == Diagnostico.Estado.ERROR and diagnostico.puntaje is None


def test_hv_sin_analizar_pide_analizarla_primero(cliente_autenticado, usuario):
    hv = crear_hv(usuario, perfil=None)
    respuesta = cliente_autenticado.post(f"/diagnostico/hv/{hv.pk}/diagnosticar/", follow=True)
    assert "Primero analiza la hoja de vida" in respuesta.content.decode()
    assert not Diagnostico.objects.exists()


def test_lista_de_hv_con_accion_diagnosticar_y_estado_vacio(cliente_autenticado, hv_demo, diagnosticar):
    assert "Diagnosticar" in cliente_autenticado.get("/diagnostico/").content.decode()
    diagnosticar(hv_demo)
    assert "86/100" in cliente_autenticado.get("/diagnostico/").content.decode()


def test_estado_vacio_sin_hojas_de_vida(cliente_autenticado):
    assert "Aún no tienes hojas de vida para diagnosticar." in cliente_autenticado.get("/diagnostico/").content.decode()


def test_no_se_ve_el_diagnostico_de_otro_usuario(client, hv_demo, diagnosticar):
    from core.pruebas.fabricas import crear_usuario

    diagnostico = diagnosticar(hv_demo)
    client.force_login(crear_usuario())
    assert client.get(f"/diagnostico/{diagnostico.pk}/").status_code == 404
    assert client.post(f"/diagnostico/hv/{hv_demo.pk}/diagnosticar/").status_code == 404
