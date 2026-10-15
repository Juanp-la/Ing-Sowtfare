"""HU17 - Plan de mejora con acciones (criterios derivados, no oficiales)."""
import pytest

from apps.preparacion import servicios
from apps.preparacion.agentes import AgenteCoach, accion_para
from core.agentes.trazador import Trazador
from core.datos_demo import PERFIL_DEMO
from core.dominio.requisitos import evaluar_requisitos
from core.llm.mock import MockLLMClient
from core.models import Diagnostico, PlanMejora, Vacante

pytestmark = pytest.mark.django_db


def _generar(cliente, hv, magneto_id):
    vacante = Vacante.objects.get(magneto_id=magneto_id)
    respuesta = cliente.post(f"/preparacion/vacante/{vacante.pk}/generar/", {"hv": hv.pk}, follow=True)
    return vacante, respuesta.content.decode()


def test_ca1_una_accion_concreta_por_cada_brecha_con_recurso_y_plazo(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, html = _generar(cliente_autenticado, hv_demo, "MAG-V-006")
    _, brechas = evaluar_requisitos(PERFIL_DEMO, vacante.requisitos)
    plan = PlanMejora.objects.get(hoja_vida=hv_demo, vacante=vacante)
    assert sorted(a["brecha"] for a in plan.acciones) == sorted(b["requisito"] for b in brechas)
    assert all(a["accion"] and a["recurso"] and a["plazo"] for a in plan.acciones)
    assert html.count('class="list-group-item px-0 accion-plan"') == len(brechas)


def test_ca2_las_brechas_obligatorias_van_primero(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, _ = _generar(cliente_autenticado, hv_demo, "MAG-V-006")
    prioridades = [a["prioridad"] for a in PlanMejora.objects.get(vacante=vacante).acciones]
    assert prioridades == sorted(prioridades, key=lambda p: p != "alta") and prioridades[0] == "alta"


def test_ca3_sin_brechas_el_plan_lo_indica(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, html = _generar(cliente_autenticado, hv_demo, "MAG-V-001")
    assert PlanMejora.objects.get(vacante=vacante).acciones == []
    assert 'id="plan-sin-brechas"' in html and "No se detectaron brechas" in html


def test_ca4_el_plan_se_guarda_asociado_a_la_hv_la_vacante_y_el_diagnostico(cliente_autenticado, hv_demo,
                                                                           vacantes_demo):
    diagnostico = Diagnostico.objects.create(hoja_vida=hv_demo, puntaje=80, estado="completado")
    vacante, _ = _generar(cliente_autenticado, hv_demo, "MAG-V-003")
    plan = PlanMejora.objects.get(hoja_vida=hv_demo, vacante=vacante)
    assert plan.diagnostico == diagnostico


def test_ca5_si_el_llm_omite_una_brecha_el_coach_la_completa():
    vacante = {"titulo": "X", "empresa": "Y", "requisitos": [
        {"tipo": "habilidad", "valor": "Rust", "obligatorio": True},
        {"tipo": "idioma", "valor": "Francés B2", "obligatorio": False}]}
    llm = MockLLMClient(respuestas={"Preparacion": {"preguntas": [], "plan": []}})
    salida = AgenteCoach(llm=llm, trazador=Trazador(persistir=False))({"perfil": PERFIL_DEMO, "vacante": vacante})
    assert [a["brecha"] for a in salida["plan"]] == ["Rust", "Francés B2"]


def test_acciones_por_tipo_de_brecha():
    for tipo, palabra in (("experiencia", "proyecto"), ("educacion", "estudios"), ("idioma", "certificación"),
                          ("habilidad", "curso")):
        accion = accion_para({"requisito": "algo", "tipo": tipo, "obligatorio": False})
        assert palabra in accion["accion"].lower() and accion["prioridad"] == "media"


def test_error_del_coach_muestra_mensaje(cliente_autenticado, hv_demo, vacantes_demo, monkeypatch):
    def fallar(*args, **kwargs):
        raise servicios.ErrorPreparacion("coach: ValueError")

    monkeypatch.setattr(servicios, "preparar", fallar)
    _, html = _generar(cliente_autenticado, hv_demo, "MAG-V-001")
    assert "El Coach no pudo generar la preparación" in html


def test_error_del_grafo_se_reporta(usuario, hv_demo, vacantes_demo):
    class Falla:
        def ejecutar(self, *a, **k):
            return {"error": "coach: ValueError"}

    with pytest.raises(servicios.ErrorPreparacion):
        servicios.preparar(usuario, hv_demo.perfil, vacantes_demo[0], servicio=Falla())
