from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules


class CoreConfig(AppConfig):
    name = "core"
    verbose_name = "Núcleo Copiloto"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import checks, signals  # noqa: F401  (registra checks y señales)

        # Cada feature registra sus nodos de LangGraph en apps/<app>/agentes.py
        autodiscover_modules("agentes")
