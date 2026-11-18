"""Cambios de núcleo acordados para el Sprint 3: menú por rol, modelos nuevos y datos de demostración."""
from io import StringIO

import pytest
from django.core.management import call_command

from core import plugins
from core.datos_demo import EMAIL_RECLUTADOR_DEMO
from core.models import HojaVida, HVAdaptada, Postulacion, Usuario, Vacante
from core.pruebas.fabricas import crear_hv, crear_usuario, crear_vacante

pytestmark = pytest.mark.django_db


def test_el_menu_filtra_por_rol(monkeypatch):
    from types import SimpleNamespace

    from django.urls import reverse

    reverse("core:inicio")  # carga las URLs reales antes de reemplazar las features
    config = SimpleNamespace(name="apps.x", label="x", menu=[
        {"titulo": "Todos", "url": "core:inicio", "orden": 1},
        {"titulo": "Solo reclutador", "url": "core:inicio", "orden": 2, "roles": ["reclutador"]}])
    candidato, reclutador = crear_usuario(), crear_usuario(rol="reclutador")
    monkeypatch.setattr(plugins, "apps_feature", lambda: [config])
    assert [e["titulo"] for e in plugins.menu(candidato)] == ["Todos"]
    assert [e["titulo"] for e in plugins.menu(reclutador)] == ["Todos", "Solo reclutador"]
    assert [e["titulo"] for e in plugins.menu()] == ["Todos"]
    admin = crear_usuario(is_superuser=True)
    assert len(plugins.menu(admin)) == 2


def test_el_reclutador_ve_su_modulo_y_no_las_opciones_del_candidato(client):
    client.force_login(crear_usuario(rol="reclutador"))
    html = client.get("/").content.decode()
    assert 'href="/reclutador/"' in html and "Mis postulaciones" not in html and "Mis hojas de vida" not in html


def test_borrar_la_hv_borra_sus_adaptaciones_y_desvincula_la_postulacion(vacantes_demo):
    usuario = crear_usuario()
    hv = crear_hv(usuario)
    vacante = vacantes_demo[0]
    HVAdaptada.objects.create(hoja_vida=hv, vacante=vacante, cambios=[{"id": "a"}])
    Postulacion.objects.create(usuario=usuario, vacante=vacante, hoja_vida=hv, perfil_enviado={"resumen": "x"})
    hv.delete()
    assert not HVAdaptada.objects.exists()
    postulacion = Postulacion.objects.get()
    assert postulacion.hoja_vida is None and postulacion.perfil_enviado == {"resumen": "x"}


def test_los_cambios_de_la_adaptacion_quedan_cifrados_en_la_bd(vacantes_demo):
    from django.db import connection

    hv = crear_hv(crear_usuario())
    adaptacion = HVAdaptada.objects.create(hoja_vida=hv, vacante=vacantes_demo[0],
                                           cambios=[{"propuesta": "Texto con SQL"}])
    with connection.cursor() as cursor:
        cursor.execute("SELECT cambios FROM core_hvadaptada WHERE id = %s", [adaptacion.pk])
        crudo = cursor.fetchone()[0]
    assert "SQL" not in crudo
    assert HVAdaptada.objects.get().cambios == [{"propuesta": "Texto con SQL"}]


def test_str_y_propiedades_de_los_modelos_nuevos():
    usuario = crear_usuario()
    vacante = crear_vacante()
    p = Postulacion.objects.create(usuario=usuario, vacante=vacante)
    assert p.abierta and not p.decidida and "enviada" in str(p)
    hv = crear_hv(usuario)
    assert "Adaptación" in str(HVAdaptada.objects.create(hoja_vida=hv, vacante=vacante))
    from core.models import AlertaVacante

    assert "Alerta" in str(AlertaVacante.objects.create(usuario=usuario, vacante=vacante, score=80))
    assert HojaVida.Origen.MAGNETO == "magneto"


def test_seed_demo_crea_reclutador_y_candidatos_postulados():
    salida = StringIO()
    call_command("seed_demo", stdout=salida)
    assert EMAIL_RECLUTADOR_DEMO in salida.getvalue()
    reclutador = Usuario.objects.get(email=EMAIL_RECLUTADOR_DEMO)
    assert reclutador.rol == "reclutador" and not Vacante.objects.filter(reclutador__isnull=True).exists()
    total = Postulacion.objects.count()
    assert total == 5
    call_command("seed_demo", stdout=StringIO())  # idempotente
    assert Postulacion.objects.count() == total
