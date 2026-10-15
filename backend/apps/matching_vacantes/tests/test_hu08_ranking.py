"""HU08 - Vacantes ordenadas por ajuste (criterios derivados, no oficiales)."""
import pytest

from apps.matching_vacantes import servicios
from apps.matching_vacantes.agentes import AgenteMatcher, puntaje_reglas
from apps.matching_vacantes.embedder import Embedder, EmbedderBolsaPalabras, obtener_embedder
from core.agentes.trazador import Trazador
from core.datos_demo import PERFIL_DEMO
from core.llm.mock import MockLLMClient
from core.models import AjusteVacante, EjecucionAgente
from core.pruebas.fabricas import crear_hv, crear_vacante

pytestmark = pytest.mark.django_db


def _orden(html):
    return [fila.split('"', 1)[0] for fila in html.split('data-vacante="')[1:]]


def test_ca1_lista_desde_bd_ordenada_por_ajuste(cliente_autenticado, hv_demo, vacantes_demo):
    html = cliente_autenticado.get("/vacantes/").content.decode()
    orden = _orden(html)
    assert len(orden) == 12
    puntajes = list(AjusteVacante.objects.filter(perfil=hv_demo.perfil).order_by("-score").values_list("score", flat=True))
    assert puntajes == sorted(puntajes, reverse=True)
    mejor = AjusteVacante.objects.get(perfil=hv_demo.perfil, vacante__magneto_id=orden[0])
    assert mejor.no_cumple == [] and mejor.score == puntajes[0]
    assert orden.index("MAG-V-001") < orden.index("MAG-V-004")  # soporte antes que backend Python


def test_ca2_cada_vacante_tiene_el_boton_ver_ajuste(cliente_autenticado, hv_demo, vacantes_demo):
    html = cliente_autenticado.get("/vacantes/").content.decode()
    assert html.count("Ver ajuste") == 12
    assert f"/vacantes/{vacantes_demo[0].pk}/?hv={hv_demo.pk}" in html


def test_ca3_sin_hv_analizada_muestra_estado_vacio(cliente_autenticado, vacantes_demo):
    html = cliente_autenticado.get("/vacantes/").content.decode()
    assert "Necesitas una hoja de vida analizada" in html and "Ver ajuste" not in html


def test_ca3_el_ajuste_se_recalcula_cuando_cambia_el_perfil(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    cliente_autenticado.get("/vacantes/")
    assert EjecucionAgente.objects.filter(agente="matcher").count() == 1
    cliente_autenticado.get("/vacantes/")
    assert EjecucionAgente.objects.filter(agente="matcher").count() == 1  # no recalcula si nada cambió
    perfil = hv_demo.perfil
    perfil.datos = {**perfil.datos, "habilidades": perfil.datos["habilidades"] + ["Python", "Django", "Git"]}
    perfil.save()
    cliente_autenticado.get("/vacantes/")
    assert EjecucionAgente.objects.filter(agente="matcher").count() == 2
    respuesta = cliente_autenticado.post("/vacantes/recalcular/", {"hv": hv_demo.pk})
    assert respuesta.url == f"/vacantes/?hv={hv_demo.pk}"
    assert EjecucionAgente.objects.filter(agente="matcher").count() == 3


def test_ca4_matcher_combina_reglas_y_similitud_con_embedder_inyectable():
    class EmbedderFijo(Embedder):
        def vectorizar(self, texto):
            return {"x": 1.0}

    vacantes = [{"id": 1, "titulo": "A", "requisitos": [{"tipo": "habilidad", "valor": "SQL", "obligatorio": True}]},
                {"id": 2, "titulo": "B", "requisitos": [{"tipo": "habilidad", "valor": "Rust", "obligatorio": True}]}]
    agente = AgenteMatcher(llm=MockLLMClient(), trazador=Trazador(persistir=False), embedder=EmbedderFijo())
    ajustes = agente({"perfil": PERFIL_DEMO, "vacantes": vacantes})["ajustes"]
    assert [a["vacante_id"] for a in ajustes] == [1, 2]
    assert ajustes[0]["score"] == 100.0 and ajustes[1]["score"] == 30.0  # 70 % reglas + 30 % similitud
    assert ajustes[0]["similitud"] == 1.0


def test_embedder_local_y_reglas_ponderadas(settings):
    embedder = EmbedderBolsaPalabras()
    assert embedder.similitud("soporte técnico SQL", "Soporte tecnico y SQL") > 0.9
    assert embedder.similitud("", "algo") == 0.0
    assert puntaje_reglas([{"obligatorio": True}], [{"obligatorio": False}]) == 2 / 3
    assert puntaje_reglas([], []) == 0.0
    settings.MATCHER_EMBEDDER = "apps.matching_vacantes.embedder.EmbedderBolsaPalabras"
    assert isinstance(obtener_embedder(), EmbedderBolsaPalabras)


def test_vacantes_inactivas_no_aparecen(cliente_autenticado, hv_demo):
    crear_vacante(magneto_id="MAG-ACTIVA", titulo="Activa")
    crear_vacante(magneto_id="MAG-CERRADA", titulo="Cerrada", activa=False)
    orden = _orden(cliente_autenticado.get("/vacantes/").content.decode())
    assert orden == ["MAG-ACTIVA"]


def test_error_del_matcher_muestra_estado_de_error(cliente_autenticado, hv_demo, vacantes_demo, monkeypatch):
    def fallar(*args, **kwargs):
        raise RuntimeError("matcher: ValueError")

    monkeypatch.setattr(servicios, "calcular_ajustes", fallar)
    assert "No fue posible calcular el ajuste" in cliente_autenticado.get("/vacantes/").content.decode()


def test_error_del_grafo_se_reporta(usuario, hv_demo, vacantes_demo):
    class Falla:
        def ejecutar(self, *a, **k):
            return {"error": "matcher: ValueError"}

    with pytest.raises(RuntimeError):
        servicios.calcular_ajustes(usuario, hv_demo.perfil, servicio=Falla())


def test_elegir_hoja_de_vida_cuando_hay_varias(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    otra = crear_hv(usuario, confirmado=False)
    html = cliente_autenticado.get(f"/vacantes/?hv={otra.pk}").content.decode()
    assert 'id="id_hv"' in html and f'<option value="{otra.pk}" selected>' in html
    assert servicios.perfil_activo(usuario, "no-numerico").pk == hv_demo.perfil.pk
