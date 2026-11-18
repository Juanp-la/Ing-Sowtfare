"""manage.py generar_alertas: revisión periódica de vacantes con alto ajuste (HU11).

Pensado para programarse (cron o tarea programada); también se ejecuta al abrir la página de alertas.
"""
from django.core.management.base import BaseCommand

from apps.matching_vacantes.servicios import generar_alertas_todos, umbral_alerta


class Command(BaseCommand):
    help = "Genera alertas de vacantes con ajuste mayor o igual al umbral para todos los candidatos."

    def add_arguments(self, parser):
        parser.add_argument("--umbral", type=float, default=None, help="Ajuste mínimo (0-100).")

    def handle(self, *args, **opciones):
        umbral = umbral_alerta() if opciones["umbral"] is None else opciones["umbral"]
        total = generar_alertas_todos(umbral=umbral)
        self.stdout.write(self.style.SUCCESS(f"Alertas nuevas: {total} (umbral {umbral:.0f} %)."))
