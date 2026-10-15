import os

import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

from core.datos_demo import TEXTO_HV_DEMO
from core.models import (
    AjusteVacante,
    Diagnostico,
    EjecucionAgente,
    Hallazgo,
    HojaVida,
    PerfilExtraido,
    PlanMejora,
    PreguntaEntrevista,
)
from core.pruebas.fabricas import crear_hv, crear_usuario, crear_vacante
from core.servicios import cifrado
from core.servicios.archivos import guardar_archivo_hv, leer_archivo_hv

pytestmark = pytest.mark.django_db


def _valor_crudo(tabla, columna, pk):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT {columna} FROM {tabla} WHERE id = %s", [pk])
        return cursor.fetchone()[0]


def test_texto_y_nombre_de_hv_se_guardan_cifrados(hv_demo):
    crudo = _valor_crudo("core_hojavida", "texto_extraido", hv_demo.pk)
    assert "ANA DEMO" not in crudo and crudo.startswith("gAAAA")
    assert "hv_sintetica" not in _valor_crudo("core_hojavida", "nombre_archivo", hv_demo.pk)
    hv = HojaVida.objects.get(pk=hv_demo.pk)
    assert hv.texto_extraido == TEXTO_HV_DEMO
    assert hv.nombre_archivo == "hv_sintetica.pdf"


def test_perfil_se_guarda_cifrado_y_se_lee_igual(hv_demo):
    crudo = _valor_crudo("core_perfilextraido", "datos", hv_demo.perfil.pk)
    assert "ana.demo@ejemplo.test" not in crudo
    assert PerfilExtraido.objects.get(pk=hv_demo.perfil.pk).datos["contacto"]["email"] == "ana.demo@ejemplo.test"


def test_dato_con_otra_clave_no_rompe_la_lectura(hv_demo, settings):
    settings.CAMPOS_CIFRADO_KEY = Fernet.generate_key().decode()
    cifrado.reiniciar()
    try:
        hv = HojaVida.objects.get(pk=hv_demo.pk)
        assert hv.texto_extraido == ""
        assert PerfilExtraido.objects.get(pk=hv_demo.perfil.pk).datos == {}
    finally:
        cifrado.reiniciar()  # la fixture settings restaura la clave de la sesión al terminar


def test_campos_vacios_y_nulos_no_se_cifran(usuario):
    hv = HojaVida.objects.create(usuario=usuario, formato="pdf")
    assert _valor_crudo("core_hojavida", "texto_extraido", hv.pk) == ""
    perfil = PerfilExtraido.objects.create(hoja_vida=hv, datos={})
    assert PerfilExtraido.objects.get(pk=perfil.pk).datos == {}
    campo = PerfilExtraido._meta.get_field("datos")
    assert campo.get_prep_value(None) is None
    assert campo.to_python('{"a": 1}') == {"a": 1}
    assert campo.to_python("no-json") == "no-json"
    assert campo.from_db_value(None, None, None) == {}
    assert '"a": 1' in campo.value_to_string(PerfilExtraido(datos={"a": 1}))


def test_clave_obligatoria_fuera_de_debug(settings, monkeypatch):
    settings.CAMPOS_CIFRADO_KEY = ""
    settings.DEBUG = False
    monkeypatch.setattr(cifrado, "_en_pruebas", lambda: False)
    cifrado.reiniciar()
    with pytest.raises(ImproperlyConfigured):
        cifrado.cifrar("x")
    settings.DEBUG = True
    cifrado.reiniciar()
    assert cifrado.descifrar(cifrado.cifrar("hola")) == "hola"  # clave efímera de desarrollo
    cifrado.reiniciar()


def test_bytes_alterados_no_se_descifran():
    assert cifrado.descifrar_bytes(b"no es fernet") is None
    assert cifrado.descifrar("no-es-token") is None


def test_archivo_hv_se_guarda_cifrado_y_se_borra_con_la_hv(usuario):
    hv = HojaVida(usuario=usuario, nombre_archivo="hv.pdf", formato="pdf")
    guardar_archivo_hv(hv, b"%PDF-1.4 contenido sintetico")
    hv.save()
    ruta = hv.archivo.path
    with open(ruta, "rb") as f:
        assert b"contenido sintetico" not in f.read()
    assert leer_archivo_hv(hv) == b"%PDF-1.4 contenido sintetico"
    assert hv.tamano_bytes == len(b"%PDF-1.4 contenido sintetico")
    hv.delete()
    assert not os.path.exists(ruta)


def test_leer_archivo_de_hv_sin_archivo(usuario):
    assert leer_archivo_hv(HojaVida(usuario=usuario, formato="pdf")) is None


def test_borrar_hv_elimina_todos_sus_datos_y_conserva_la_traza_sin_pii(usuario):
    hv = crear_hv(usuario)
    vacante = crear_vacante()
    diagnostico = Diagnostico.objects.create(hoja_vida=hv, puntaje=70, nivel="por_mejorar")
    Hallazgo.objects.create(diagnostico=diagnostico, categoria="contacto", descripcion="d", prioridad="alta")
    AjusteVacante.objects.create(perfil=hv.perfil, vacante=vacante, score=50)
    PlanMejora.objects.create(hoja_vida=hv, vacante=vacante, acciones=[{"accion": "x"}])
    PreguntaEntrevista.objects.create(hoja_vida=hv, vacante=vacante, pregunta="¿?")
    traza = EjecucionAgente.objects.create(usuario=usuario, hoja_vida=hv, agente="extractor", tokens=10)

    hv.delete()

    for modelo in (HojaVida, PerfilExtraido, Diagnostico, Hallazgo, AjusteVacante, PlanMejora, PreguntaEntrevista):
        assert modelo.objects.count() == 0
    traza.refresh_from_db()
    assert traza.hoja_vida_id is None and traza.tokens == 10


def test_hallazgos_se_ordenan_por_prioridad(hv_demo):
    diagnostico = Diagnostico.objects.create(hoja_vida=hv_demo)
    for prioridad in ("baja", "alta", "media"):
        Hallazgo.objects.create(diagnostico=diagnostico, categoria=prioridad, descripcion="d", prioridad=prioridad)
    assert [h.prioridad for h in diagnostico.hallazgos.all()] == ["alta", "media", "baja"]


def test_representaciones_de_texto(usuario, hv_demo):
    vacante = crear_vacante(titulo="Analista", empresa="Ficticia")
    diagnostico = Diagnostico.objects.create(hoja_vida=hv_demo)
    hallazgo = Hallazgo.objects.create(diagnostico=diagnostico, categoria="c", descripcion="d", prioridad="alta")
    ajuste = AjusteVacante.objects.create(perfil=hv_demo.perfil, vacante=vacante, score=61.4)
    plan = PlanMejora.objects.create(hoja_vida=hv_demo)
    pregunta = PreguntaEntrevista.objects.create(hoja_vida=hv_demo, vacante=vacante, pregunta="¿Qué es SQL?")
    traza = EjecucionAgente.objects.create(agente="matcher", duracion_ms=5)
    assert str(usuario) == usuario.email
    assert str(hv_demo).startswith("HV ")
    assert "Perfil" in str(hv_demo.perfil)
    assert "Diagnóstico" in str(diagnostico)
    assert str(hallazgo) == "[alta] c"
    assert str(vacante) == "Analista - Ficticia"
    assert str(ajuste).startswith("Ajuste 61")
    assert str(plan).startswith("Plan")
    assert str(pregunta) == "¿Qué es SQL?"
    assert str(traza) == "matcher (ok) 5 ms"


def test_nombre_visible_del_usuario(db):
    assert crear_usuario(nombre="Ana Sintética").nombre_visible == "Ana Sintética"
    sin_nombre = crear_usuario(email="sin.nombre@copiloto.test", nombre="")
    assert sin_nombre.nombre_visible == "sin.nombre"
