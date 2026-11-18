"""HU11 - Alertas de vacantes nuevas con alto ajuste (criterios derivados, por validar con el PO)."""
import pytest
from django.core.management import call_command

from apps.matching_vacantes import servicios
from core.models import AlertaVacante
from core.pruebas.fabricas import crear_hv, crear_usuario, crear_vacante

pytestmark = pytest.mark.django_db


def test_ca1_vacantes_con_ajuste_mayor_al_umbral_generan_alerta(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    html = cliente_autenticado.get("/vacantes/alertas/").content.decode()
    alertas = list(AlertaVacante.objects.filter(usuario=usuario))
    assert alertas and all(a.score >= servicios.umbral_alerta() for a in alertas)
    assert 'id="alertas-nuevas"' in html and html.count('class="fila-alerta') == len(alertas)
    assert [a.score for a in alertas] == sorted((a.score for a in alertas), reverse=True)


def test_ca2_no_se_repite_la_alerta_de_una_vacante_ya_avisada(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    cliente_autenticado.get("/vacantes/alertas/")
    total = AlertaVacante.objects.filter(usuario=usuario).count()
    html = cliente_autenticado.get("/vacantes/alertas/").content.decode()
    assert AlertaVacante.objects.filter(usuario=usuario).count() == total and 'id="alertas-nuevas"' not in html


def test_ca3_una_vacante_nueva_con_alto_ajuste_avisa_en_la_barra(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    cliente_autenticado.get("/vacantes/alertas/")
    AlertaVacante.objects.filter(usuario=usuario).update(leida=True)
    nueva = crear_vacante(titulo="Analista de soporte nivel 2", requisitos=[
        {"tipo": "habilidad", "valor": "SQL", "obligatorio": True},
        {"tipo": "habilidad", "valor": "Zendesk", "obligatorio": True}])
    assert [a.vacante for a in servicios.generar_alertas(usuario)] == [nueva]
    html = cliente_autenticado.get("/").content.decode()
    assert 'id="indicador-alertas"' in html and "1 alerta<" in html.replace("\n", "").replace("  ", "")


def test_ca4_vacantes_con_bajo_ajuste_no_generan_alerta(usuario, hv_demo, vacantes_demo):
    baja = crear_vacante(titulo="Piloto", requisitos=[{"tipo": "habilidad", "valor": "Aviación", "obligatorio": True}])
    servicios.generar_alertas(usuario)
    assert not AlertaVacante.objects.filter(usuario=usuario, vacante=baja).exists()


def test_ca5_marcar_una_o_todas_como_leidas(cliente_autenticado, usuario, hv_demo, vacantes_demo):
    cliente_autenticado.get("/vacantes/alertas/")
    primera = AlertaVacante.objects.filter(usuario=usuario).first()
    cliente_autenticado.post(f"/vacantes/alertas/{primera.pk}/leida/")
    primera.refresh_from_db()
    assert primera.leida
    cliente_autenticado.post("/vacantes/alertas/leidas/")
    assert not AlertaVacante.objects.filter(usuario=usuario, leida=False).exists()
    assert 'id="indicador-alertas"' not in cliente_autenticado.get("/").content.decode()


def test_ca6_sin_hv_analizada_muestra_estado_vacio(cliente_autenticado, vacantes_demo):
    html = cliente_autenticado.get("/vacantes/alertas/").content.decode()
    assert "Necesitas una hoja de vida analizada para recibir alertas" in html


def test_no_puedo_marcar_alertas_de_otro_usuario(client, cliente_autenticado, usuario, hv_demo, vacantes_demo):
    cliente_autenticado.get("/vacantes/alertas/")
    ajena = AlertaVacante.objects.filter(usuario=usuario).first()
    otro = crear_usuario()
    client.force_login(otro)
    assert client.post(f"/vacantes/alertas/{ajena.pk}/leida/").status_code == 404


def test_comando_generar_alertas_revisa_a_todos_los_candidatos(vacantes_demo, capsys):
    a, b = crear_usuario(), crear_usuario()
    crear_hv(a)
    crear_hv(b)
    call_command("generar_alertas", "--umbral", "70")
    assert AlertaVacante.objects.filter(usuario=a).count() == AlertaVacante.objects.filter(usuario=b).count() > 0
    assert "Alertas nuevas:" in capsys.readouterr().out


def test_el_comando_no_falla_si_un_candidato_no_tiene_cuota(vacantes_demo):
    sin_cuota = crear_usuario(cuota_tokens_mes=0)
    crear_hv(sin_cuota)
    assert servicios.generar_alertas_todos(umbral=70) == 0


def test_error_del_grafo_se_informa_en_la_pagina(cliente_autenticado, hv_demo, vacantes_demo, monkeypatch):
    def fallar(*args, **kwargs):
        raise RuntimeError("matcher: ValueError")

    monkeypatch.setattr(servicios, "generar_alertas", fallar)
    html = cliente_autenticado.get("/vacantes/alertas/").content.decode()
    assert "No fue posible revisar vacantes nuevas" in html
