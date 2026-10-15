"""HU01 - Iniciar sesión con cuenta Magneto. Un test por criterio de aceptación (oficial, Entrega 1 §3.4)."""
import pytest
from django.contrib.auth.hashers import make_password

from apps.acceso_magneto import views
from apps.acceso_magneto.clientes import MagnetoMockClient
from core.models import Usuario
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


@pytest.fixture
def cuenta_magneto(clave):
    return crear_usuario(email="candidata@magneto.test", clave=clave, nombre="Laura Sintética", magneto_id="MAG-100")


def test_ca1_sin_sesion_redirige_al_inicio_de_sesion_de_magneto(client):
    respuesta = client.get("/", follow=True)
    assert respuesta.redirect_chain[-1][0] == "/magneto/ingresar/?next=%2F"
    assert "Ingresa con tu cuenta de Magneto" in respuesta.content.decode()


def test_ca2_credenciales_invalidas_muestran_mensaje_y_conservan_el_correo(client, cuenta_magneto):
    respuesta = client.post("/magneto/ingresar/", {"email": "candidata@magneto.test", "clave": "equivocada"})
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Usuario o contraseña incorrectos" in html
    assert 'value="candidata@magneto.test"' in html
    assert "_auth_user_id" not in client.session


def test_ca2_correo_inexistente_o_vacio_da_el_mismo_mensaje(client):
    for datos in ({"email": "nadie@magneto.test", "clave": "x"}, {"email": "", "clave": ""}):
        assert "Usuario o contraseña incorrectos" in client.post("/magneto/ingresar/", datos).content.decode()


def test_ca3_con_sesion_valida_el_copiloto_muestra_el_nombre_del_candidato(client, cuenta_magneto, clave):
    respuesta = client.post("/magneto/ingresar/", {"email": "candidata@magneto.test", "clave": clave, "next": "/"}, follow=True)
    assert respuesta.redirect_chain[-1][0] == "/"
    assert "Hola, Laura Sintética" in respuesta.content.decode()


def test_ingreso_no_crea_otro_usuario_y_vincula_por_magneto_id(client, monkeypatch, clave):
    directorio = MagnetoMockClient(cuentas=[{"magneto_id": "MAG-200", "nombre": "Pedro Sintético",
                                             "email": "pedro@magneto.test", "clave_hash": make_password(clave)}])
    monkeypatch.setattr(views, "obtener_cliente_magneto", lambda: directorio)
    client.post("/magneto/ingresar/", {"email": "pedro@magneto.test", "clave": clave})
    usuario = Usuario.objects.get(magneto_id="MAG-200")
    assert usuario.nombre == "Pedro Sintético" and not usuario.has_usable_password()
    client.logout()
    client.post("/magneto/ingresar/", {"email": "PEDRO@magneto.test", "clave": clave})
    assert Usuario.objects.filter(magneto_id="MAG-200").count() == 1


def test_next_externo_se_ignora_y_usuario_autenticado_no_ve_el_login(client, cuenta_magneto, clave):
    respuesta = client.post("/magneto/ingresar/", {"email": "candidata@magneto.test", "clave": clave,
                                                   "next": "https://sitio-externo.test/"})
    assert respuesta.url == "/"
    assert client.get("/magneto/ingresar/?next=/magneto/consumo/").url == "/magneto/consumo/"


def test_salir_vuelve_al_login_de_magneto(client, cuenta_magneto, clave):
    client.post("/magneto/ingresar/", {"email": "candidata@magneto.test", "clave": clave})
    respuesta = client.post("/cuenta/salir/", follow=True)
    assert respuesta.redirect_chain[-1][0].startswith("/magneto/ingresar/")
