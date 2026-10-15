"""NF02 - Datos cifrados y borrables (criterios derivados, no oficiales)."""
import os

import pytest
from django.db import connection

from core.models import EjecucionAgente, HojaVida, PerfilExtraido
from core.pruebas.fabricas import crear_hv, crear_usuario

from .utilidades import subir_y_analizar

pytestmark = pytest.mark.django_db


def _crudo(tabla, columna, pk):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {columna} FROM {tabla} WHERE id = %s", [pk])
        return cursor.fetchone()[0]


def test_ca1_datos_personales_cifrados_en_bd_y_en_disco(cliente_autenticado):
    hv, _ = subir_y_analizar(cliente_autenticado)
    for valor in (_crudo("core_hojavida", "texto_extraido", hv.pk), _crudo("core_hojavida", "nombre_archivo", hv.pk),
                  _crudo("core_perfilextraido", "datos", hv.perfil.pk)):
        assert valor.startswith("gAAAA") and "ana.demo" not in valor and "Ana" not in valor
    with open(hv.archivo.path, "rb") as f:
        assert not f.read().startswith(b"%PDF")
    assert not os.path.basename(hv.archivo.name).startswith("hv_sintetica")


def test_ca2_eliminar_hv_borra_todos_sus_datos_desde_la_lista(cliente_autenticado, usuario):
    hv, _ = subir_y_analizar(cliente_autenticado)
    ruta = hv.archivo.path
    lista = cliente_autenticado.get("/hv/").content.decode()
    assert f"/hv/{hv.pk}/eliminar/" in lista
    assert "no se puede deshacer" in cliente_autenticado.get(f"/hv/{hv.pk}/eliminar/").content.decode()

    respuesta = cliente_autenticado.post(f"/hv/{hv.pk}/eliminar/", follow=True)

    assert "fueron eliminados" in respuesta.content.decode()
    assert not HojaVida.objects.filter(pk=hv.pk).exists()
    assert not PerfilExtraido.objects.filter(hoja_vida_id=hv.pk).exists()
    assert not os.path.exists(ruta)
    assert EjecucionAgente.objects.filter(usuario=usuario, hoja_vida__isnull=True).exists()  # traza sin PII queda


def test_ca3_nadie_puede_ver_ni_borrar_la_hv_de_otro(cliente_autenticado):
    ajena = crear_hv(crear_usuario())
    for url in (f"/hv/{ajena.pk}/", f"/hv/{ajena.pk}/perfil/", f"/hv/{ajena.pk}/eliminar/"):
        assert cliente_autenticado.get(url).status_code == 404
    assert cliente_autenticado.post(f"/hv/{ajena.pk}/eliminar/").status_code == 404
    assert HojaVida.objects.filter(pk=ajena.pk).exists()


def test_lista_vacia_muestra_estado_vacio(cliente_autenticado):
    assert "Aún no has cargado tu hoja de vida." in cliente_autenticado.get("/hv/").content.decode()
