import pytest

from apps.acceso_magneto import clientes
from apps.acceso_magneto.clientes import MagnetoMockClient
from core.models import Vacante


@pytest.fixture
def magneto():
    cliente = MagnetoMockClient(cuentas=[])
    clientes.establecer_cliente_magneto(cliente)
    yield cliente
    clientes.establecer_cliente_magneto(None)


@pytest.fixture
def candidato_magneto(usuario):
    usuario.magneto_id = "MAG-T-CAND-1"
    usuario.save()
    return usuario


@pytest.fixture
def vacante_soporte(vacantes_demo):
    return Vacante.objects.get(magneto_id="MAG-V-001")
