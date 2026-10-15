"""Punto de extensión de features (plug-in).

Una feature es una carpeta backend/apps/<app>/ cuyo AppConfig puede declarar:
  prefijo_url        "hv/"                     prefijo de sus URLs (por defecto "<label>/")
  menu               [{"titulo", "url", "orden"}] entradas del menú de base.html
  fragmentos_navbar  ["<app>/partials/x.html"]   plantillas que se incluyen en la barra superior
  url_login          "<app>:ingresar"          reemplaza el login mínimo del núcleo
"""
from django.apps import apps
from django.urls import NoReverseMatch, reverse


def apps_feature():
    return [c for c in apps.get_app_configs() if c.name.startswith("apps.")]


def prefijo_url(config):
    return getattr(config, "prefijo_url", f"{config.label}/")


def menu():
    entradas = []
    for config in apps_feature():
        for item in getattr(config, "menu", []):
            try:
                url = reverse(item["url"])
            except NoReverseMatch:
                continue
            entradas.append({"titulo": item["titulo"], "url": url, "orden": item.get("orden", 100)})
    return sorted(entradas, key=lambda e: (e["orden"], e["titulo"]))


def fragmentos_navbar():
    return [f for config in apps_feature() for f in getattr(config, "fragmentos_navbar", [])]


def url_login_externa():
    for config in apps_feature():
        nombre = getattr(config, "url_login", None)
        if nombre:
            return reverse(nombre)
    return None
