from django.apps import AppConfig


class PostulacionesConfig(AppConfig):
    """Feature 6: postulación desde el copiloto y seguimiento (HU15, HU18)."""

    name = "apps.postulaciones"
    label = "postulaciones"
    verbose_name = "Postulación y seguimiento"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "postulaciones/"
    menu = [{"titulo": "Mis postulaciones", "url": "postulaciones:lista", "orden": 60,
             "roles": ["candidato", "admin"]}]
