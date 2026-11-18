from django.apps import AppConfig


class AdaptacionHvConfig(AppConfig):
    """Feature 5: adaptación de la HV a una vacante con el agente Redactor (HU12, HU13, HU14)."""

    name = "apps.adaptacion_hv"
    label = "adaptacion_hv"
    verbose_name = "Adaptación de HV (agente Redactor)"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "adaptacion/"
    menu = [{"titulo": "Adaptar HV", "url": "adaptacion_hv:inicio", "orden": 45, "roles": ["candidato", "admin"]}]
