"""HU04 - Usar la HV que ya está en el perfil de Magneto (criterios derivados, por validar con el PO)."""
import pytest

from apps.acceso_magneto import clientes
from apps.acceso_magneto.clientes import ArchivoHVMagneto, MagnetoMockClient
from apps.acceso_magneto.servicios import importar_hv_magneto
from core.datos_demo import MAGNETO_ID_DEMO, TEXTO_HV_DEMO
from core.models import HojaVida
from core.pruebas.fabricas import crear_usuario, pdf_bytes
from core.servicios.archivos import leer_archivo_hv

pytestmark = pytest.mark.django_db

MAGNETO_ID = "MAG-T-HV-1"


@pytest.fixture
def archivo():
    return ArchivoHVMagneto("HV_en_Magneto.pdf", "pdf", pdf_bytes(TEXTO_HV_DEMO), "2026-11-01")


@pytest.fixture
def candidato(client, archivo):
    usuario = crear_usuario(magneto_id=MAGNETO_ID)
    clientes.establecer_cliente_magneto(MagnetoMockClient(hojas_vida={MAGNETO_ID: archivo}))
    client.force_login(usuario)
    yield usuario
    clientes.establecer_cliente_magneto(None)


def test_ca1_si_tengo_hv_en_magneto_la_veo_con_el_boton_usar(client, candidato):
    html = client.get("/magneto/hv/").content.decode()
    assert "HV_en_Magneto.pdf" in html and 'id="btn-usar-hv-magneto"' in html and "2026-11-01" in html


def test_ca2_al_usarla_queda_en_el_copiloto_sin_cargarla_y_lista_para_analizar(client, candidato, archivo):
    respuesta = client.post("/magneto/hv/importar/")
    hv = HojaVida.objects.get(usuario=candidato)
    assert respuesta.status_code == 302 and respuesta["Location"] == f"/hv/{hv.pk}/"
    assert hv.origen == HojaVida.Origen.MAGNETO and hv.huella == archivo.huella and hv.formato == "pdf"
    assert leer_archivo_hv(hv) == archivo.contenido
    with hv.archivo.open("rb") as en_disco:
        assert not en_disco.read().startswith(b"%PDF")  # en disco queda cifrado (NF02)
    respuesta = client.post(f"/hv/{hv.pk}/analizar/", follow=True)
    hv.refresh_from_db()
    assert hv.estado == HojaVida.Estado.ANALIZADA and "SQL" in hv.perfil.datos["habilidades"]


def test_ca3_sin_hv_en_magneto_se_informa_y_se_ofrece_cargar(client):
    usuario = crear_usuario(magneto_id="MAG-SIN-HV")
    clientes.establecer_cliente_magneto(MagnetoMockClient(hojas_vida={}))
    client.force_login(usuario)
    try:
        html = client.get("/magneto/hv/").content.decode()
        assert "No encontramos una hoja de vida en tu perfil de Magneto." in html and "/hv/cargar/" in html
        html = client.post("/magneto/hv/importar/", follow=True).content.decode()
        assert "No encontramos una hoja de vida" in html and not HojaVida.objects.filter(usuario=usuario).exists()
    finally:
        clientes.establecer_cliente_magneto(None)


def test_ca4_no_se_duplica_si_ya_la_habia_traido(client, candidato):
    client.post("/magneto/hv/importar/")
    html = client.post("/magneto/hv/importar/", follow=True).content.decode()
    assert HojaVida.objects.filter(usuario=candidato).count() == 1
    assert "ya estaba en el copiloto" in html
    assert 'id="ya-importada"' in client.get("/magneto/hv/").content.decode()


def test_la_lista_de_hv_ofrece_magneto_y_marca_el_origen(client, candidato):
    client.post("/magneto/hv/importar/")
    html = client.get("/hv/").content.decode()
    assert 'id="btn-hv-magneto"' in html and ">Magneto</span>" in html


def test_cliente_simulado_por_defecto_trae_la_hv_sintetica_de_la_demo():
    archivo = MagnetoMockClient().obtener_hv(MAGNETO_ID_DEMO)
    assert archivo.formato == "pdf" and archivo.contenido.startswith(b"%PDF") and len(archivo.huella) == 64
    assert MagnetoMockClient().obtener_hv("NO-EXISTE") is None and MagnetoMockClient().obtener_hv("") is None


def test_servicio_sin_magneto_id_no_importa_nada():
    usuario = crear_usuario()
    assert importar_hv_magneto(usuario, MagnetoMockClient()) == (None, False)
