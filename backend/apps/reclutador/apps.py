from django.apps import AppConfig


class ReclutadorConfig(AppConfig):
    """Feature 8: módulo reclutador (HU19, HU20)."""

    name = "apps.reclutador"
    label = "reclutador"
    verbose_name = "Módulo reclutador"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "reclutador/"
    menu = [{"titulo": "Mis vacantes", "url": "reclutador:inicio", "orden": 10,
             "roles": ["reclutador", "admin"]}]
