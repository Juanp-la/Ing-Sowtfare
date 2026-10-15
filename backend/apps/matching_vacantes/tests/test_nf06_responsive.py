"""NF06 - Uso desde el celular: interfaz responsive con Bootstrap 5 (criterios derivados, no oficiales)."""
import re

import pytest
from django.conf import settings

PLANTILLAS = settings.FRONTEND_DIR / "templates"


def test_ca1_base_tiene_viewport_bootstrap_y_menu_colapsable():
    base = (PLANTILLAS / "base.html").read_text(encoding="utf-8")
    navbar = (PLANTILLAS / "partials" / "_navbar.html").read_text(encoding="utf-8")
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in base
    assert "bootstrap@5" in base and "bootstrap.bundle.min.js" in base
    assert "navbar-expand-lg" in navbar and "navbar-toggler" in navbar and 'class="collapse navbar-collapse"' in navbar


def test_ca2_toda_tabla_es_desplazable_o_apilable_en_celular():
    for plantilla in PLANTILLAS.rglob("*.html"):
        html = plantilla.read_text(encoding="utf-8")
        for _ in re.finditer(r"<table", html):
            assert "table-responsive" in html and "tabla-apilable" in html, plantilla.name
            assert "data-etiqueta=" in html, plantilla.name


def test_ca3_las_plantillas_de_feature_extienden_base_y_usan_rejilla_fluida():
    for plantilla in PLANTILLAS.rglob("*.html"):
        if plantilla.parent.name in ("partials", "templates") or "partials" in plantilla.parts:
            continue
        html = plantilla.read_text(encoding="utf-8")
        assert html.startswith('{% extends "base.html" %}'), plantilla.name
        assert not re.search(r"width:\s*\d{3,}px", html), plantilla.name


def test_ca4_css_apila_tablas_en_pantallas_pequenas():
    css = (settings.FRONTEND_DIR / "static" / "css" / "app.css").read_text(encoding="utf-8")
    assert "@media (max-width: 575.98px)" in css and ".tabla-apilable td::before" in css


@pytest.mark.django_db
def test_ca5_vistas_de_vacantes_se_renderizan_con_clases_responsivas(cliente_autenticado, hv_demo, vacantes_demo):
    lista = cliente_autenticado.get("/vacantes/").content.decode()
    assert "col-12 col-sm-6 col-md-3" in lista and "table-responsive" in lista and 'data-etiqueta="Ajuste"' in lista
    detalle = cliente_autenticado.get(f"/vacantes/{vacantes_demo[0].pk}/").content.decode()
    assert "col-12 col-md-6" in detalle and "flex-column flex-md-row" in detalle
