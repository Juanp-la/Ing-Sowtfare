"""HU12 - Adaptar la HV a una vacante específica (criterios derivados, por validar con el PO)."""
import pytest

from apps.adaptacion_hv import servicios
from apps.adaptacion_hv.agentes import AgenteRedactor, cambios_por_reglas, relevancia
from core.agentes.trazador import Trazador
from core.datos_demo import PERFIL_DEMO
from core.models import EjecucionAgente, HVAdaptada, PerfilExtraido

pytestmark = pytest.mark.django_db


def test_ca1_lista_de_vacantes_con_accion_adaptar(cliente_autenticado, hv_demo, vacantes_demo):
    html = cliente_autenticado.get("/adaptacion/").content.decode()
    assert 'id="tabla-vacantes-adaptar"' in html and html.count(">Adaptar mi HV</a>") == len(vacantes_demo)


def test_ca2_el_redactor_propone_cambios_orientados_a_la_vacante(adaptacion):
    por_id = {c["id"]: c for c in adaptacion.cambios}
    assert por_id["habilidades"]["propuesta"][:3] == ["SQL", "Zendesk", "Soporte técnico"]
    assert sorted(por_id["habilidades"]["propuesta"]) == sorted(PERFIL_DEMO["habilidades"])  # nada agregado
    assert "SQL" in por_id["resumen"]["propuesta"] and por_id["resumen"]["original"] == PERFIL_DEMO["resumen"]
    assert set(por_id["palabras_clave"]["propuesta"]) <= {"SQL", "Zendesk", "Inglés B1"}
    assert all(c["motivo"] and c["decision"] == "" for c in adaptacion.cambios)


def test_ca3_la_propuesta_queda_pendiente_y_no_toca_la_hv_original(adaptacion, hv_demo):
    assert adaptacion.estado == HVAdaptada.Estado.PENDIENTE
    assert PerfilExtraido.objects.get(hoja_vida=hv_demo).datos == PERFIL_DEMO


def test_ca4_queda_trazado_que_agente_genero_la_propuesta(adaptacion):
    agentes = list(EjecucionAgente.objects.filter(ejecucion_id=adaptacion.ejecucion_id).values_list("agente", flat=True))
    assert {"supervisor", "redactor", "validador_redactor"} <= set(agentes)


def test_ca5_sin_hv_analizada_no_se_puede_adaptar(cliente_autenticado, vacantes_demo):
    html = cliente_autenticado.get(f"/adaptacion/vacante/{vacantes_demo[0].pk}/").content.decode()
    assert "Necesitas una hoja de vida analizada" in html
    respuesta = cliente_autenticado.post(f"/adaptacion/vacante/{vacantes_demo[0].pk}/generar/", follow=True)
    assert "Necesitas una hoja de vida analizada" in respuesta.content.decode() and not HVAdaptada.objects.exists()


def test_regenerar_reemplaza_la_propuesta_pendiente(cliente_autenticado, hv_demo, vacante_soporte, adaptacion):
    cliente_autenticado.post(f"/adaptacion/vacante/{vacante_soporte.pk}/generar/", {"hv": hv_demo.pk})
    assert HVAdaptada.objects.filter(hoja_vida=hv_demo, vacante=vacante_soporte).count() == 1
    html = cliente_autenticado.get(f"/adaptacion/vacante/{vacante_soporte.pk}/?hv={hv_demo.pk}").content.decode()
    assert "Ya tienes una adaptación para esta vacante" in html


def test_sin_nada_que_cambiar_se_informa(cliente_autenticado, hv_demo, vacantes_demo):
    from core.pruebas.fabricas import crear_vacante

    vacante = crear_vacante(requisitos=[{"tipo": "educacion", "valor": "bachiller", "obligatorio": True}])
    html = cliente_autenticado.post(f"/adaptacion/vacante/{vacante.pk}/generar/", {"hv": hv_demo.pk},
                                    follow=True).content.decode()
    assert "no hay cambios que proponer" in html


def test_error_del_redactor_muestra_mensaje(cliente_autenticado, hv_demo, vacante_soporte, monkeypatch):
    def fallar(*args, **kwargs):
        raise servicios.ErrorAdaptacion("redactor: ValueError")

    monkeypatch.setattr(servicios, "adaptar", fallar)
    html = cliente_autenticado.post(f"/adaptacion/vacante/{vacante_soporte.pk}/generar/", {"hv": hv_demo.pk},
                                    follow=True).content.decode()
    assert "El Redactor no pudo adaptar tu hoja de vida" in html


def test_error_del_grafo_se_reporta(usuario, hv_demo, vacante_soporte):
    class Falla:
        def ejecutar(self, *a, **k):
            return {"error": "redactor: ValueError"}

    with pytest.raises(servicios.ErrorAdaptacion):
        servicios.adaptar(usuario, hv_demo.perfil, vacante_soporte, servicio=Falla())


def test_reglas_reordenan_la_experiencia_por_relevancia():
    perfil = {"experiencia": [{"cargo": "Cajero", "empresa": "A", "periodo": "2020"},
                              {"cargo": "Analista de datos", "empresa": "B", "periodo": "2021",
                               "descripcion": "Reportes en Python"}]}
    vacante = {"titulo": "Analista", "requisitos": [{"tipo": "habilidad", "valor": "Python", "obligatorio": True}]}
    cambio = next(c for c in cambios_por_reglas(perfil, vacante) if c["id"] == "experiencia")
    assert cambio["propuesta"][0].startswith("Analista de datos")
    assert relevancia("texto sin relación", vacante["requisitos"]) == 0


def test_resumen_vacio_recibe_una_propuesta():
    perfil = {"resumen": "", "habilidades": ["SQL"]}
    vacante = {"requisitos": [{"tipo": "habilidad", "valor": "SQL", "obligatorio": True}]}
    cambio = next(c for c in cambios_por_reglas(perfil, vacante) if c["id"] == "resumen")
    assert cambio["propuesta"] == "Dominio de SQL."


def test_el_agente_funciona_fuera_del_grafo():
    vacante = {"titulo": "X", "requisitos": [{"tipo": "habilidad", "valor": "Zendesk", "obligatorio": True}]}
    salida = AgenteRedactor(trazador=Trazador(persistir=False))({"perfil": PERFIL_DEMO, "vacante": vacante})
    assert salida["datos"]["adaptacion"][0]["propuesta"][0] == "Zendesk"
