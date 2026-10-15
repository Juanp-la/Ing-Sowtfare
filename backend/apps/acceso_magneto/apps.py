from django.apps import AppConfig


class AccesoMagnetoConfig(AppConfig):
    """Feature 1: acceso e integración con Magneto (HU01, NF04)."""

    name = "apps.acceso_magneto"
    label = "acceso_magneto"
    verbose_name = "Acceso e integración Magneto"
    default_auto_field = "django.db.models.BigAutoField"
    prefijo_url = "magneto/"
    url_login = "acceso_magneto:ingresar"
    menu = [{"titulo": "Mi consumo", "url": "acceso_magneto:consumo", "orden": 90}]
    fragmentos_navbar = ["acceso_magneto/partials/cuota_navbar.html"]
