import pytest

from core.models import Vacante


@pytest.fixture
def vacante_soporte(vacantes_demo):
    return Vacante.objects.get(magneto_id="MAG-V-001")


@pytest.fixture
def adaptacion(cliente_autenticado, hv_demo, vacante_soporte):
    from core.models import HVAdaptada

    cliente_autenticado.post(f"/adaptacion/vacante/{vacante_soporte.pk}/generar/", {"hv": hv_demo.pk})
    return HVAdaptada.objects.get(hoja_vida=hv_demo, vacante=vacante_soporte)
