"""NF03 aplicado al Redactor: la adaptación nunca agrega experiencia, habilidades ni cifras que no estén en la HV."""
import pytest

from apps.adaptacion_hv import servicios
from core.llm.mock import MockLLMClient
from core.models import HVAdaptada
from core.servicios.copiloto import CopilotoService

pytestmark = pytest.mark.django_db


def _llm_que_inventa(prompt, borrador):
    cambios = [dict(c) for c in borrador["cambios"]]
    for c in cambios:
        if c["id"] == "habilidades":
            c["propuesta"] = ["Python", "Power BI", *c["propuesta"]]
        if c["id"] == "resumen":
            c["propuesta"] = c["propuesta"] + " Con 10 años en Python y Django."
    cambios.append({"id": "extra", "seccion": "palabras_clave", "titulo": "Más", "original": [],
                    "propuesta": ["Kubernetes"], "motivo": "inventado"})
    return {"cambios": cambios}


def test_ca1_el_validador_quita_habilidades_y_cifras_inventadas(usuario, hv_demo, vacantes_demo):
    vacante = vacantes_demo[0]
    servicio = CopilotoService(llm=MockLLMClient(respuestas={"AdaptacionHV": _llm_que_inventa}))
    adaptacion = servicios.adaptar(usuario, hv_demo.perfil, vacante, servicio=servicio)
    por_id = {c["id"]: c for c in adaptacion.cambios}
    assert "Python" not in por_id["habilidades"]["propuesta"] and "Power BI" not in por_id["habilidades"]["propuesta"]
    assert "resumen" not in por_id  # el resumen con «10 años en Python» se descarta completo
    assert "extra" not in por_id  # un cambio que solo trae datos inventados desaparece


def test_ca2_lo_que_si_esta_en_la_hv_se_conserva(usuario, hv_demo, vacantes_demo):
    adaptacion = servicios.adaptar(usuario, hv_demo.perfil, vacantes_demo[0])
    texto = hv_demo.texto_extraido
    for cambio in adaptacion.cambios:
        if isinstance(cambio["propuesta"], list):
            assert all(item.split(" - ")[0].lower() in texto.lower() for item in cambio["propuesta"])
    assert HVAdaptada.objects.count() == 1
