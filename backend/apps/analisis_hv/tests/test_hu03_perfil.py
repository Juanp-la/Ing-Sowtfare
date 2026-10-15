"""HU03 - Ver y corregir datos extraídos. Criterios oficiales (Entrega 1 §3.4)."""
import pytest

from core.models import PerfilExtraido
from core.pruebas.fabricas import pdf_bytes

from .utilidades import subir_y_analizar

pytestmark = pytest.mark.django_db

HV_INCOMPLETA = """CARLOS SINTETICO PRUEBA
Cali | carlos.sintetico@ejemplo.test

EXPERIENCIA
Mesero - Restaurante Ficticio (2023 - 2024)

HABILIDADES
Atención al cliente, Trabajo en equipo
"""


def test_ca1_tras_el_analisis_muestra_los_campos_extraidos(cliente_autenticado):
    hv, respuesta = subir_y_analizar(cliente_autenticado)
    html = respuesta.content.decode()
    assert respuesta.redirect_chain[-1][0] == f"/hv/{hv.pk}/perfil/"
    for esperado in ("Datos de contacto", "ana.demo@ejemplo.test", "Analista de soporte | Empresa Ficticia XYZ",
                     "Tecnología en Sistemas de Información", "SQL, Windows Server", "Inglés B1"):
        assert esperado in html
    assert PerfilExtraido.objects.get(hoja_vida=hv).confirmado is False


def test_ca2_todo_campo_vacio_se_resalta_y_es_editable(cliente_autenticado):
    _, respuesta = subir_y_analizar(cliente_autenticado, "incompleta.pdf", pdf_bytes(HV_INCOMPLETA))
    html = respuesta.content.decode()
    campo_telefono = html.split('id="id_telefono"')[0].rsplit("<input", 1)[1]
    assert "campo-vacio" in campo_telefono
    assert 'name="educacion" id="id_educacion"' in html and "Campo vacío" in html
    campo_nombre = html.split('id="id_nombre"')[0].rsplit("<input", 1)[1]
    assert "campo-vacio" not in campo_nombre


def test_ca3_los_cambios_se_guardan_solo_al_confirmar(cliente_autenticado):
    hv, _ = subir_y_analizar(cliente_autenticado)
    url = f"/hv/{hv.pk}/perfil/"
    datos = {"nombre": "Ana Demo Restrepo", "email": "ana.demo@ejemplo.test", "telefono": "3000000000",
             "ciudad": "Envigado", "resumen": "Resumen corregido", "experiencia": "Analista | Empresa | 2022 - 2025 | Soporte",
             "educacion": "Tecnología | Institución | 2021", "habilidades": "SQL, Excel", "idiomas": "Inglés B1"}

    revisar = cliente_autenticado.post(url, {**datos, "accion": "revisar"})
    assert 'id="cambios-sin-guardar"' in revisar.content.decode()
    perfil = PerfilExtraido.objects.get(hoja_vida=hv)
    assert perfil.datos["contacto"]["ciudad"] == "Medellín" and not perfil.confirmado

    confirmar = cliente_autenticado.post(url, {**datos, "accion": "confirmar"})
    assert confirmar.status_code == 302 and confirmar.url == "/hv/"
    perfil.refresh_from_db()
    assert perfil.confirmado and perfil.datos["contacto"]["ciudad"] == "Envigado"
    assert perfil.datos["experiencia"][0] == {"cargo": "Analista", "empresa": "Empresa", "periodo": "2022 - 2025",
                                              "descripcion": "Soporte"}
    assert perfil.datos["habilidades"] == ["SQL", "Excel"]


def test_formulario_invalido_no_guarda(cliente_autenticado):
    hv, _ = subir_y_analizar(cliente_autenticado)
    respuesta = cliente_autenticado.post(f"/hv/{hv.pk}/perfil/", {"email": "no-es-correo", "accion": "confirmar"})
    assert respuesta.status_code == 200 and not PerfilExtraido.objects.get(hoja_vida=hv).confirmado


def test_perfil_sin_analizar_muestra_estado_vacio(cliente_autenticado):
    from .utilidades import subir

    subir(cliente_autenticado)
    from core.models import HojaVida

    hv = HojaVida.objects.latest("id")
    assert "aún no se ha analizado" in cliente_autenticado.get(f"/hv/{hv.pk}/perfil/").content.decode()
