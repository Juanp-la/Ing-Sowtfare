from django.apps import AppConfig


class MatchingVacantesConfig(AppConfig):
    """Feature 4: matching de vacantes con el agente Matcher (HU08, HU09, HU10, NF06)."""

    name = "apps.matching_vacantes"
    label = "matching_vacantes"
    verbose_name = "Matching de vacantes (agente Matcher)"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "vacantes/"
    menu = [{"titulo": "Vacantes", "url": "matching_vacantes:lista", "orden": 40}]
