from django.apps import AppConfig


class PreparacionConfig(AppConfig):
    """Feature 7: preparación con el agente Coach (HU16, HU17)."""

    name = "apps.preparacion"
    label = "preparacion"
    verbose_name = "Preparación (agente Coach)"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "preparacion/"
    menu = [{"titulo": "Preparación", "url": "preparacion:inicio", "orden": 50}]
