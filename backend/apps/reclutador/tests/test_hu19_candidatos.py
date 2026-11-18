"""HU19 - Ver los candidatos postulados ordenados por ajuste (criterios derivados, por validar con el PO)."""
import pytest

from core.models import Postulacion, Vacante
from core.pruebas.fabricas import crear_usuario

pytestmark = pytest.mark.django_db


def test_ca1_veo_mis_vacantes_con_el_numero_de_postulados(cliente_reclutador, vacante_con_postulados):
    html = cliente_reclutador.get("/reclutador/").content.decode()
    assert html.count('class="fila-vacante-reclutador"') == 1  # solo las vacantes asignadas a este reclutador
    assert 'class="postulados">3<' in html and "Ver candidatos" in html


def test_ca2_los_candidatos_aparecen_del_mayor_al_menor_ajuste(cliente_reclutador, vacante_con_postulados):
    html = cliente_reclutador.get(f"/reclutador/vacante/{vacante_con_postulados.pk}/").content.decode()
    posiciones = [html.index(n) for n in ("Carlos Sintético Gómez", "Mateo Sintético Ruiz", "Luisa Sintética Pérez")]
    assert posiciones == sorted(posiciones)
    scores = list(Postulacion.objects.filter(vacante=vacante_con_postulados).order_by("-score")
                  .values_list("score", flat=True))
    assert scores == sorted(scores, reverse=True) and scores[0] > scores[-1]


def test_ca3_cada_candidato_muestra_ajuste_requisitos_y_accion_evaluar(cliente_reclutador, vacante_con_postulados):
    html = cliente_reclutador.get(f"/reclutador/vacante/{vacante_con_postulados.pk}/").content.decode()
    assert html.count('class="fila-candidato"') == 3 and html.count(">Evaluar</a>") == 3
    assert f"de {len(vacante_con_postulados.requisitos)}" in html


def test_ca4_puedo_filtrar_candidatos_por_estado(cliente_reclutador, vacante_con_postulados):
    mejor = Postulacion.objects.filter(vacante=vacante_con_postulados).order_by("-score").first()
    mejor.estado = Postulacion.Estado.APTO
    mejor.save()
    html = cliente_reclutador.get(f"/reclutador/vacante/{vacante_con_postulados.pk}/?estado=apto").content.decode()
    assert html.count('class="fila-candidato"') == 1 and "Carlos Sintético Gómez" in html


def test_ca5_un_candidato_no_entra_al_modulo_reclutador(cliente_autenticado, vacante_con_postulados):
    assert cliente_autenticado.get("/reclutador/").status_code == 403
    assert cliente_autenticado.get(f"/reclutador/vacante/{vacante_con_postulados.pk}/").status_code == 403
    assert 'href="/reclutador/"' not in cliente_autenticado.get("/").content.decode()


def test_ca6_no_veo_vacantes_de_otro_reclutador(client, vacante_con_postulados):
    otro = crear_usuario(rol="reclutador")
    client.force_login(otro)
    assert client.get(f"/reclutador/vacante/{vacante_con_postulados.pk}/").status_code == 404
    assert "Aún no tienes vacantes asignadas" in client.get("/reclutador/").content.decode()


def test_el_administrador_ve_todas_las_vacantes(client, vacante_con_postulados):
    admin = crear_usuario(rol="admin")
    client.force_login(admin)
    html = client.get("/reclutador/").content.decode()
    assert html.count('class="fila-vacante-reclutador"') == Vacante.objects.count()


def test_vacante_sin_postulados_muestra_estado_vacio(cliente_reclutador, reclutador, vacantes_demo):
    vacante = vacantes_demo[5]
    vacante.reclutador = reclutador
    vacante.save()
    html = cliente_reclutador.get(f"/reclutador/vacante/{vacante.pk}/").content.decode()
    assert "Todavía no hay candidatos postulados" in html
