from django.apps import AppConfig


class DiagnosticoHvConfig(AppConfig):
    """Feature 3: diagnóstico de HV con el agente Evaluador (HU05, HU06, HU07, NF01, NF05)."""

    name = "apps.diagnostico_hv"
    label = "diagnostico_hv"
    verbose_name = "Diagnóstico de HV (agente Evaluador)"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "diagnostico/"
    menu = [
        {"titulo": "Diagnóstico", "url": "diagnostico_hv:inicio", "orden": 30},
        {"titulo": "Trazabilidad", "url": "diagnostico_hv:trazabilidad", "orden": 80},
    ]
