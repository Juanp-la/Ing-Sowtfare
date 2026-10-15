from django.conf import settings
from django.core.checks import Error, Warning, register

COMANDO_CLAVE = 'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'


@register()
def revisar_clave_cifrado(app_configs, **kwargs):
    if settings.CAMPOS_CIFRADO_KEY:
        return []
    if not settings.DEBUG:
        return [
            Error(
                "CAMPOS_CIFRADO_KEY es obligatoria con DJANGO_DEBUG=0.",
                hint=f"Genérela con: {COMANDO_CLAVE} y guárdela en .env",
                id="core.E001",
            )
        ]
    return [
        Warning(
            "CAMPOS_CIFRADO_KEY no está definida: se usa una clave efímera y los datos cifrados "
            "no sobreviven a un reinicio del servidor.",
            hint=f"Genérela con: {COMANDO_CLAVE} y guárdela en .env",
            id="core.W001",
        )
    ]
