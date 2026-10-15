from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AjusteVacante,
    Diagnostico,
    EjecucionAgente,
    Hallazgo,
    HojaVida,
    PerfilExtraido,
    PlanMejora,
    PreguntaEntrevista,
    Usuario,
    Vacante,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("email", "nombre", "rol", "magneto_id", "cuota_tokens_mes", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Copiloto", {"fields": ("nombre", "rol", "magneto_id", "cuota_tokens_mes")}),)


@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "ciudad", "modalidad", "salario_min", "salario_max", "activa")
    list_filter = ("ciudad", "modalidad", "activa")


@admin.register(EjecucionAgente)
class EjecucionAgenteAdmin(admin.ModelAdmin):
    list_display = ("fecha", "agente", "estado", "tokens", "duracion_ms", "usuario")
    list_filter = ("agente", "estado")
    readonly_fields = [f.name for f in EjecucionAgente._meta.fields]


for modelo in (HojaVida, PerfilExtraido, Diagnostico, Hallazgo, AjusteVacante, PlanMejora, PreguntaEntrevista):
    admin.site.register(modelo)
