import pytest

from apps.acceso_magneto import clientes
from apps.acceso_magneto.clientes import MagnetoMockClient
from apps.postulaciones.servicios import postular
from core.datos_demo import CANDIDATOS_POSTULADOS_DEMO
from core.models import Usuario, Vacante
from core.pruebas.fabricas import crear_hv, crear_usuario


@pytest.fixture
def magneto():
    cliente = MagnetoMockClient(cuentas=[])
    clientes.establecer_cliente_magneto(cliente)
    yield cliente
    clientes.establecer_cliente_magneto(None)


@pytest.fixture
def reclutador(db):
    return crear_usuario(rol=Usuario.Rol.RECLUTADOR, magneto_id="MAG-T-REC")


@pytest.fixture
def cliente_reclutador(client, reclutador):
    client.force_login(reclutador)
    return client


@pytest.fixture
def vacante_con_postulados(vacantes_demo, reclutador, magneto):
    """MAG-V-001 con tres candidatos sintéticos de distinto ajuste."""
    vacante = Vacante.objects.get(magneto_id="MAG-V-001")
    vacante.reclutador = reclutador
    vacante.save()
    for datos in CANDIDATOS_POSTULADOS_DEMO:
        candidato = crear_usuario(nombre=datos["nombre"], magneto_id=datos["magneto_id"])
        hv = crear_hv(candidato, perfil=datos["perfil"])
        postular(candidato, vacante, perfil=hv.perfil, cliente=magneto)
    return vacante
