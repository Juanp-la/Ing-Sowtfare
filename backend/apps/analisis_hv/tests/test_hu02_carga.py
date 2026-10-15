"""HU02 - Cargar HV en PDF o Word. Criterios oficiales (Entrega 1 §3.4)."""
import pytest

from core.models import HojaVida
from core.validadores import MENSAJE_FORMATO_NO_ADMITIDO

from .utilidades import subir

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("nombre", ["hv_sintetica.pdf", "hv_sintetica.docx"])
def test_ca1_acepta_pdf_y_docx_de_maximo_5_mb(cliente_autenticado, usuario, nombre):
    respuesta = subir(cliente_autenticado, nombre)
    hv = HojaVida.objects.get(usuario=usuario)
    assert respuesta.status_code == 302 and respuesta.url == f"/hv/{hv.pk}/"
    assert hv.formato == nombre.rsplit(".", 1)[1] and hv.tamano_bytes > 0


@pytest.mark.parametrize(
    "nombre,contenido",
    [("hv.txt", b"texto"), ("hv.png", b"\x89PNG"), ("hv.pdf", b"no soy un pdf"), ("hv.doc", b"\xd0\xcf\x11\xe0")],
)
def test_ca2_otra_extension_muestra_mensaje_y_conserva_la_pantalla_de_carga(cliente_autenticado, nombre, contenido):
    respuesta = subir(cliente_autenticado, nombre, contenido)
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert MENSAJE_FORMATO_NO_ADMITIDO in html and 'id="form-carga"' in html
    assert HojaVida.objects.count() == 0


def test_ca2_archivo_de_mas_de_5_mb_muestra_mensaje(cliente_autenticado, settings):
    settings.HV_TAMANO_MAXIMO = 1024  # mismo validador, límite reducido para no generar 5 MB en la prueba
    respuesta = subir(cliente_autenticado, "grande.pdf", b"%PDF-1.4" + b"0" * 2048)
    assert MENSAJE_FORMATO_NO_ADMITIDO in respuesta.content.decode() and HojaVida.objects.count() == 0


def test_ca2_envio_sin_archivo_conserva_la_pantalla(cliente_autenticado):
    respuesta = cliente_autenticado.post("/hv/cargar/", {})
    assert respuesta.status_code == 200 and MENSAJE_FORMATO_NO_ADMITIDO in respuesta.content.decode()


def test_ca3_al_cargar_muestra_el_nombre_y_habilita_analizar(cliente_autenticado):
    pantalla = cliente_autenticado.get("/hv/cargar/").content.decode()
    assert 'id="btn-analizar" disabled' in pantalla
    detalle = subir(cliente_autenticado, "mi_hv_2026.pdf")
    html = cliente_autenticado.get(detalle.url).content.decode()
    assert 'id="nombre-archivo">mi_hv_2026.pdf<' in html
    assert 'id="btn-analizar">Analizar<' in html and "disabled" not in html.split('id="btn-analizar"')[1][:20]


def test_carga_requiere_sesion(client):
    assert client.get("/hv/cargar/").status_code == 302
