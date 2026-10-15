import logging
from io import StringIO
from types import SimpleNamespace

import pytest
from django.conf import settings as conf
from django.core.management import call_command
from django.test import RequestFactory
from django.urls import reverse

from core import checks, plugins
from core.context_processors import copiloto
from core.datos_demo import EMAIL_DEMO
from core.middleware import CuotaAgotadaMiddleware
from core.models import HojaVida, Usuario, Vacante
from core.registro_logs import FiltroSinPII, enmascarar
from core.servicios.cuota import CuotaAgotada

pytestmark = pytest.mark.django_db


@pytest.fixture
def sin_login_externo(monkeypatch):
    monkeypatch.setattr(plugins, "url_login_externa", lambda: None)


def test_inicio_sin_sesion_redirige_a_ingresar(client):
    respuesta = client.get("/")
    assert respuesta.status_code == 302 and respuesta.url.startswith("/cuenta/ingresar/?next=/")


def test_login_minimo_por_correo(client, usuario, clave, sin_login_externo):
    respuesta = client.post("/cuenta/ingresar/", {"username": usuario.email, "password": clave})
    assert respuesta.status_code == 302
    inicio = client.get("/")
    assert usuario.nombre_visible in inicio.content.decode()


def test_login_minimo_con_credenciales_invalidas(client, usuario, sin_login_externo):
    respuesta = client.post("/cuenta/ingresar/", {"username": usuario.email, "password": "incorrecta"})
    assert respuesta.status_code == 200 and usuario.email in respuesta.content.decode()


def test_login_delega_en_la_feature_que_declara_url_login(client, monkeypatch):
    monkeypatch.setattr(plugins, "url_login_externa", lambda: "/externo/ingresar/")
    assert client.get("/cuenta/ingresar/?next=/hv/").url == "/externo/ingresar/?next=%2Fhv%2F"
    assert client.get("/cuenta/ingresar/?next=https://malicioso.test/").url == "/externo/ingresar/"


def test_salir_requiere_post(cliente_autenticado):
    assert cliente_autenticado.get("/cuenta/salir/").status_code == 405
    assert cliente_autenticado.post("/cuenta/salir/").status_code == 302
    assert cliente_autenticado.get("/").status_code == 302


def test_auto_login_demo_solo_con_debug_y_bandera(client, settings, sin_login_externo):
    Usuario.objects.create_user(email=EMAIL_DEMO, username="demo", password=None, nombre="Demo")
    settings.DEBUG = True
    settings.DEV_AUTO_LOGIN = True
    assert client.get("/").status_code == 200
    client.logout()
    settings.DEV_AUTO_LOGIN = False
    assert client.get("/").status_code == 302


def test_middleware_de_cuota_muestra_aviso(usuario):
    peticion = RequestFactory().get("/")
    peticion.user = usuario
    middleware = CuotaAgotadaMiddleware(lambda r: None)
    respuesta = middleware.process_exception(peticion, CuotaAgotada("sin cupo"))
    assert respuesta.status_code == 429 and "sin cupo" in respuesta.content.decode()
    assert middleware.process_exception(peticion, ValueError()) is None
    assert middleware(peticion) is None


def test_plugins_menu_fragmentos_y_login(monkeypatch):
    falsa = SimpleNamespace(
        label="falsa", name="apps.falsa", prefijo_url="falsa/",
        menu=[{"titulo": "Inicio", "url": "core:inicio", "orden": 1}, {"titulo": "Rota", "url": "no:existe"}],
        fragmentos_navbar=["partials/_pie.html"], url_login="core:inicio",
    )
    monkeypatch.setattr(plugins, "apps_feature", lambda: [falsa])
    assert plugins.menu() == [{"titulo": "Inicio", "url": "/", "orden": 1}]
    assert plugins.fragmentos_navbar() == ["partials/_pie.html"]
    assert plugins.url_login_externa() == "/"
    assert plugins.prefijo_url(SimpleNamespace(label="x")) == "x/"
    contexto = copiloto(None)
    assert contexto["nombre_app"] == "Magneto Copiloto" and contexto["menu_copiloto"][0]["titulo"] == "Inicio"


def test_settings_descubre_las_apps_de_feature():
    carpetas = sorted(p.parent.name for p in (conf.BASE_DIR / "apps").glob("*/apps.py"))
    assert conf.FEATURE_APPS == [f"apps.{c}" for c in carpetas]
    assert all(app in conf.INSTALLED_APPS for app in conf.FEATURE_APPS)
    for config in plugins.apps_feature():
        assert reverse("core:inicio") == "/"
        assert plugins.prefijo_url(config).endswith("/")


def test_checks_de_clave_de_cifrado(settings):
    settings.CAMPOS_CIFRADO_KEY = ""
    settings.DEBUG = True
    assert checks.revisar_clave_cifrado(None)[0].id == "core.W001"
    settings.DEBUG = False
    assert checks.revisar_clave_cifrado(None)[0].id == "core.E001"
    settings.CAMPOS_CIFRADO_KEY = "definida"
    assert checks.revisar_clave_cifrado(None) == []


def test_logs_enmascaran_correos_y_telefonos():
    assert enmascarar("Escribir a ana.demo@ejemplo.test o al +57 300 000 0000") == "Escribir a [correo] o al [telefono]"
    registro = logging.LogRecord("x", logging.INFO, __file__, 1, "correo %s", ("a@b.co",), None)
    assert FiltroSinPII().filter(registro) and registro.getMessage() == "correo [correo]"


def test_seed_demo_crea_datos_sinteticos_e_imprime_credenciales():
    salida = StringIO()
    call_command("seed_demo", stdout=salida)
    texto = salida.getvalue()
    assert EMAIL_DEMO in texto and "clave" in texto
    usuario = Usuario.objects.get(email=EMAIL_DEMO)
    assert usuario.magneto_id and Vacante.objects.count() == 12
    hv = HojaVida.objects.get(usuario=usuario)
    assert hv.perfil.confirmado and hv.archivo
    call_command("seed_demo", stdout=StringIO())  # idempotente
    assert HojaVida.objects.filter(usuario=usuario).count() == 1 and Vacante.objects.count() == 12


def test_seed_demo_avisa_si_falta_la_clave_de_cifrado(settings):
    settings.CAMPOS_CIFRADO_KEY = ""
    salida = StringIO()
    call_command("seed_demo", "--sin-hv", stdout=salida)
    assert "CAMPOS_CIFRADO_KEY" in salida.getvalue()


def test_base_es_responsive(cliente_autenticado):
    html = cliente_autenticado.get("/").content.decode()
    assert 'name="viewport"' in html and "navbar-toggler" in html and "bootstrap@5" in html
