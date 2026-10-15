import copy

import pytest

from core.datos_demo import PERFIL_DEMO
from core.models import Diagnostico


@pytest.fixture(autouse=True)
def _on_commit_inmediato(monkeypatch):
    """Las pruebas corren dentro de una transacción: se ejecuta el callback de on_commit en el acto."""
    from django.db import transaction

    monkeypatch.setattr(transaction, "on_commit", lambda funcion, *a, **k: funcion())


@pytest.fixture
def diagnosticar(cliente_autenticado):
    def _diagnosticar(hv):
        cliente_autenticado.post(f"/diagnostico/hv/{hv.pk}/diagnosticar/")
        return Diagnostico.objects.filter(hoja_vida=hv).latest("id")

    return _diagnosticar


@pytest.fixture
def perfil_debil():
    perfil = copy.deepcopy(PERFIL_DEMO)
    perfil["contacto"]["telefono"] = ""
    perfil["contacto"]["email"] = ""
    perfil["resumen"] = ""
    perfil["experiencia"][1]["empresa"] = ""
    perfil["educacion"] = [{"titulo": "Bachiller", "institucion": "", "anio": ""}]
    perfil["habilidades"] = ["Excel"]
    perfil["idiomas"] = ["Inglés"]
    return perfil
