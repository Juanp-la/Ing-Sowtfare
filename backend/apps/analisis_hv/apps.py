from django.apps import AppConfig


class AnalisisHvConfig(AppConfig):
    """Feature 2: análisis de HV con el agente Extractor (HU02, HU03, NF02, NF03)."""

    name = "apps.analisis_hv"
    label = "analisis_hv"
    verbose_name = "Análisis de HV (agente Extractor)"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "hv/"
    menu = [{"titulo": "Mis hojas de vida", "url": "analisis_hv:lista", "orden": 20}]
