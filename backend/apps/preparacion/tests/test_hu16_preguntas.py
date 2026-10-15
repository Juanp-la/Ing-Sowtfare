"""HU16 - Preguntas probables de entrevista (criterios derivados, no oficiales)."""
import pytest

from core.models import EjecucionAgente, PreguntaEntrevista, Vacante

pytestmark = pytest.mark.django_db


def _generar(cliente, hv, magneto_id):
    vacante = Vacante.objects.get(magneto_id=magneto_id)
    respuesta = cliente.post(f"/preparacion/vacante/{vacante.pk}/generar/", {"hv": hv.pk}, follow=True)
    return vacante, respuesta.content.decode()


def test_ca1_preguntas_generadas_desde_la_vacante_y_las_brechas(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, html = _generar(cliente_autenticado, hv_demo, "MAG-V-003")  # brechas: Python, Power BI, profesional...
    preguntas = list(PreguntaEntrevista.objects.filter(hoja_vida=hv_demo, vacante=vacante))
    tipos = [p.tipo for p in preguntas]
    assert "tecnica" in tipos and "brecha" in tipos and "conductual" in tipos
    assert any("SQL" in p.pregunta for p in preguntas if p.tipo == "tecnica")
    assert {p.brecha for p in preguntas if p.tipo == "brecha"} == {"Python", "Power BI", "profesional"}
    assert "DatosNorte (ficticia)" in preguntas[-1].pregunta
    assert html.count('class="mb-2 pregunta"') == len(preguntas)


def test_ca2_cada_pregunta_trae_una_sugerencia_para_responder(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, html = _generar(cliente_autenticado, hv_demo, "MAG-V-001")
    preguntas = PreguntaEntrevista.objects.filter(vacante=vacante)
    assert preguntas.exists() and all(p.sugerencia for p in preguntas)
    assert html.count("Cómo responder:") == preguntas.count()
    assert "Analista de soporte" in preguntas.first().sugerencia  # usa la experiencia real del candidato


def test_ca3_se_guardan_y_al_regenerar_se_reemplazan(cliente_autenticado, hv_demo, vacantes_demo):
    vacante, _ = _generar(cliente_autenticado, hv_demo, "MAG-V-002")
    cantidad = PreguntaEntrevista.objects.filter(vacante=vacante).count()
    html = cliente_autenticado.get(f"/preparacion/vacante/{vacante.pk}/").content.decode()
    assert "Regenerar preguntas y plan" in html
    _generar(cliente_autenticado, hv_demo, "MAG-V-002")
    assert PreguntaEntrevista.objects.filter(vacante=vacante).count() == cantidad
    assert EjecucionAgente.objects.filter(agente="coach").count() == 2


def test_ca4_sin_hv_analizada_muestra_estado_vacio(cliente_autenticado, vacantes_demo):
    assert "Necesitas una hoja de vida analizada" in cliente_autenticado.get("/preparacion/").content.decode()
    vacante = vacantes_demo[0]
    assert "Necesitas una hoja de vida analizada" in \
        cliente_autenticado.get(f"/preparacion/vacante/{vacante.pk}/").content.decode()
    assert cliente_autenticado.post(f"/preparacion/vacante/{vacante.pk}/generar/").status_code == 302
    assert not PreguntaEntrevista.objects.exists()


def test_lista_de_vacantes_con_accion_preparar(cliente_autenticado, hv_demo, vacantes_demo):
    html = cliente_autenticado.get("/preparacion/").content.decode()
    assert html.count(">Preparar<") == 12 and 'id="tabla-preparacion"' in html


def test_sin_vacantes_activas_y_vacante_cerrada(cliente_autenticado, hv_demo):
    from core.pruebas.fabricas import crear_vacante

    assert "No hay vacantes activas" in cliente_autenticado.get("/preparacion/").content.decode()
    cerrada = crear_vacante(activa=False)
    assert cliente_autenticado.get(f"/preparacion/vacante/{cerrada.pk}/").status_code == 404


def test_vacante_sin_preparacion_invita_a_generarla(cliente_autenticado, hv_demo, vacantes_demo):
    html = cliente_autenticado.get(f"/preparacion/vacante/{vacantes_demo[0].pk}/").content.decode()
    assert "Aún no has generado tu preparación" in html


def test_elegir_hoja_de_vida_cuando_hay_varias(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    from apps.preparacion.servicios import perfil_activo
    from core.pruebas.fabricas import crear_hv

    otra = crear_hv(usuario, confirmado=False)
    html = cliente_autenticado.get(f"/preparacion/?hv={otra.pk}").content.decode()
    assert f'<option value="{otra.pk}" selected>' in html
    assert perfil_activo(usuario, "x").pk == hv_demo.perfil.pk
