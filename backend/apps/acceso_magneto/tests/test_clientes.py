import pytest
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ImproperlyConfigured

from apps.acceso_magneto.clientes import MagnetoMockClient, PerfilMagneto, obtener_cliente_magneto
from apps.acceso_magneto.servicios import vincular_usuario
from apps.acceso_magneto.templatetags.cuota_tags import resumen_cuota
from core.pruebas.fabricas import crear_usuario


def test_mock_en_memoria_autentica_y_obtiene_perfil(clave):
    cliente = MagnetoMockClient(cuentas=[{"magneto_id": "M1", "nombre": "Sintética", "email": "s@magneto.test",
                                          "clave_hash": make_password(clave)}])
    assert cliente.autenticar("S@magneto.test", clave) == PerfilMagneto("M1", "Sintética", "s@magneto.test")
    assert cliente.autenticar("s@magneto.test", "otra") is None
    assert cliente.autenticar("s@magneto.test", "") is None
    assert cliente.obtener_perfil("M1").email == "s@magneto.test"
    assert cliente.obtener_perfil("M9") is None


@pytest.mark.django_db
def test_mock_por_defecto_usa_las_cuentas_sinteticas_de_la_bd(clave):
    crear_usuario(email="demo2@magneto.test", clave=clave, magneto_id="M2", nombre="Demo Dos")
    crear_usuario(email="sin.magneto@copiloto.test", clave=clave)
    cliente = obtener_cliente_magneto()
    assert cliente.autenticar("demo2@magneto.test", clave).magneto_id == "M2"
    assert cliente.autenticar("sin.magneto@copiloto.test", clave) is None  # sin cuenta Magneto
    assert cliente.obtener_perfil("M2").nombre == "Demo Dos"
    assert cliente.obtener_perfil("M404") is None


def test_cliente_real_no_existe_en_sprint_2(settings):
    settings.MAGNETO_CLIENT = "real"
    with pytest.raises(ImproperlyConfigured):
        obtener_cliente_magneto()


@pytest.mark.django_db
def test_vincular_usuario_existente_por_correo():
    existente = crear_usuario(email="ya@copiloto.test")
    vinculado = vincular_usuario(PerfilMagneto("M3", "Nombre Magneto", "ya@copiloto.test"))
    assert vinculado.pk == existente.pk and vinculado.magneto_id == "M3"


def test_etiqueta_de_cuota_sin_sesion():
    class Anonimo:
        is_authenticated = False

    assert resumen_cuota(Anonimo()) is None
