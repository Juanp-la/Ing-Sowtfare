"""HU06 - Hallazgos priorizados. Criterios oficiales (Entrega 1 §3.4)."""
import copy

import pytest

from core.datos_demo import PERFIL_DEMO
from core.pruebas.fabricas import crear_hv

pytestmark = pytest.mark.django_db


def test_ca1_hallazgos_ordenados_por_prioridad_maximo_cinco_con_accion(cliente_autenticado, usuario, diagnosticar,
                                                                       perfil_debil):
    diagnostico = diagnosticar(crear_hv(usuario, perfil=perfil_debil))
    prioridades = [h.prioridad for h in diagnostico.hallazgos.all()]
    assert len(prioridades) > 5
    assert prioridades == sorted(prioridades, key={"alta": 1, "media": 2, "baja": 3}.get)

    pagina1 = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert pagina1.count('class="list-group-item hallazgo"') == 5
    assert pagina1.count("Acción sugerida:") == 5
    assert pagina1.index(">Alta<") < pagina1.index(">Media<")
    pagina2 = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/?pagina=2").content.decode()
    assert pagina2.count('class="list-group-item hallazgo"') == len(prioridades) - 5


def test_ca2_sin_hallazgos_muestra_que_cumple_los_criterios_basicos(cliente_autenticado, usuario, diagnosticar):
    perfil = copy.deepcopy(PERFIL_DEMO)
    perfil["experiencia"][0]["descripcion"] += " Atendí 120 incidentes al mes."
    perfil["experiencia"][1]["descripcion"] += " Reduje 30% los tiempos."
    perfil["habilidades"] += ["Linux", "Redes"]
    diagnostico = diagnosticar(crear_hv(usuario, perfil=perfil))
    html = cliente_autenticado.get(f"/diagnostico/{diagnostico.pk}/").content.decode()
    assert diagnostico.hallazgos.count() == 0 and diagnostico.puntaje == 100
    assert "Tu hoja de vida cumple los criterios básicos" in html
