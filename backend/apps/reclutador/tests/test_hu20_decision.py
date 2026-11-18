"""HU20 - Marcar apto o no apto y que alimente la retroalimentación (criterios derivados, por validar con el PO)."""
import pytest

from apps.reclutador import servicios
from core.models import Postulacion
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


@pytest.fixture
def luisa(vacante_con_postulados):
    return Postulacion.objects.get(vacante=vacante_con_postulados, usuario__nombre="Luisa Sintética Pérez")


@pytest.fixture
def carlos(vacante_con_postulados):
    return Postulacion.objects.get(vacante=vacante_con_postulados, usuario__nombre="Carlos Sintético Gómez")


def test_ca1_al_abrir_la_postulacion_el_candidato_la_ve_en_revision(cliente_reclutador, luisa):
    html = cliente_reclutador.get(f"/reclutador/postulacion/{luisa.pk}/").content.decode()
    luisa.refresh_from_db()
    assert luisa.estado == Postulacion.Estado.EN_REVISION and 'id="perfil-enviado"' in html


def test_ca2_marcar_no_apto_exige_comentario(cliente_reclutador, luisa):
    html = cliente_reclutador.post(f"/reclutador/postulacion/{luisa.pk}/", {"decision": "no_apto"}).content.decode()
    luisa.refresh_from_db()
    assert 'id="error-comentario"' in html and luisa.estado != Postulacion.Estado.NO_APTO


def test_ca3_no_apto_genera_retroalimentacion_por_cada_requisito_no_cumplido(cliente_reclutador, luisa):
    cliente_reclutador.post(f"/reclutador/postulacion/{luisa.pk}/",
                            {"decision": "no_apto", "comentario": "Falta experiencia con SQL."})
    luisa.refresh_from_db()
    assert luisa.estado == Postulacion.Estado.NO_APTO and luisa.comentario_reclutador == "Falta experiencia con SQL."
    assert [r["requisito"] for r in luisa.retroalimentacion] == [
        r["requisito"] for r in sorted(luisa.no_cumple, key=lambda r: not r["obligatorio"])]
    assert all(r["sugerencia"] for r in luisa.retroalimentacion)


def test_ca4_el_candidato_ve_la_decision_en_su_seguimiento(client, cliente_reclutador, luisa):
    cliente_reclutador.post(f"/reclutador/postulacion/{luisa.pk}/",
                            {"decision": "no_apto", "comentario": "Falta experiencia con SQL."})
    client.force_login(luisa.usuario)
    html = client.get(f"/postulaciones/{luisa.pk}/").content.decode()
    assert "No apto" in html and "Falta experiencia con SQL." in html and 'class="item-retro"' in html


def test_ca5_apto_resalta_los_puntos_fuertes(cliente_reclutador, carlos):
    cliente_reclutador.post(f"/reclutador/postulacion/{carlos.pk}/", {"decision": "apto"})
    carlos.refresh_from_db()
    assert carlos.estado == Postulacion.Estado.APTO
    assert carlos.retroalimentacion and all("puntos fuertes" in r["sugerencia"] for r in carlos.retroalimentacion)


def test_ca6_la_decision_se_puede_corregir(cliente_reclutador, carlos):
    cliente_reclutador.post(f"/reclutador/postulacion/{carlos.pk}/", {"decision": "apto"})
    html = cliente_reclutador.get(f"/reclutador/postulacion/{carlos.pk}/").content.decode()
    assert 'value="apto"' in html and "checked" in html
    cliente_reclutador.post(f"/reclutador/postulacion/{carlos.pk}/", {"decision": "no_apto", "comentario": "Cambió."})
    carlos.refresh_from_db()
    assert carlos.estado == Postulacion.Estado.NO_APTO


def test_ca7_un_candidato_no_puede_decidir(cliente_autenticado, usuario, luisa):
    assert cliente_autenticado.post(f"/reclutador/postulacion/{luisa.pk}/", {"decision": "apto"}).status_code == 403
    with pytest.raises(PermissionError):
        servicios.decidir(usuario, luisa, "apto")


def test_otro_reclutador_no_ve_la_postulacion(client, luisa):
    client.force_login(crear_usuario(rol="reclutador"))
    assert client.get(f"/reclutador/postulacion/{luisa.pk}/").status_code == 404


def test_decision_invalida_se_rechaza(reclutador, luisa):
    with pytest.raises(ValueError):
        servicios.decidir(reclutador, luisa, "en_revision")


def test_no_apto_sin_brechas_usa_el_comentario(reclutador, carlos):
    carlos.no_cumple = []
    servicios.decidir(reclutador, carlos, "no_apto", "Se eligió a otro perfil.")
    assert carlos.retroalimentacion == [{"requisito": "Comentario del reclutador", "sugerencia": "Se eligió a otro perfil."}]
