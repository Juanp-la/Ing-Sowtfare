"""ControlCuota (NF04): cuota mensual de tokens por usuario, verificada antes de invocar el grafo.

El consumo se calcula sumando los tokens de EjecucionAgente del mes en curso.
"""
from django.db.models import Sum
from django.utils import timezone


class CuotaAgotada(Exception):
    """El usuario ya consumió su cuota mensual de tokens."""


class ControlCuota:
    def inicio_mes(self, ahora=None):
        ahora = timezone.localtime(ahora or timezone.now())
        return ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def consumo_mes(self, usuario, ahora=None):
        from ..models import EjecucionAgente

        total = EjecucionAgente.objects.filter(usuario=usuario, fecha__gte=self.inicio_mes(ahora)).aggregate(
            total=Sum("tokens")
        )["total"]
        return total or 0

    def disponible(self, usuario):
        return max(0, usuario.cuota_tokens_mes - self.consumo_mes(usuario))

    def porcentaje_usado(self, usuario):
        if not usuario.cuota_tokens_mes:
            return 100
        return min(100, round(self.consumo_mes(usuario) * 100 / usuario.cuota_tokens_mes))

    def verificar(self, usuario):
        return self.disponible(usuario) > 0

    def resumen(self, usuario):
        consumo = self.consumo_mes(usuario)
        return {
            "cuota": usuario.cuota_tokens_mes,
            "consumo": consumo,
            "disponible": max(0, usuario.cuota_tokens_mes - consumo),
            "porcentaje": self.porcentaje_usado(usuario),
            "agotada": consumo >= usuario.cuota_tokens_mes,
        }

    def registrar_consumo(self, usuario, tokens, agente="consumo_manual"):
        from ..models import EjecucionAgente

        return EjecucionAgente.objects.create(usuario=usuario, agente=agente, tokens=max(0, int(tokens)))
