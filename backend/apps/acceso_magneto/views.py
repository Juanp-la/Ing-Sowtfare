from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from core.servicios.cuota import ControlCuota

from .clientes import obtener_cliente_magneto
from .forms import IngresoMagnetoForm
from .servicios import consumo_por_agente, vincular_usuario

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos"


def _siguiente(request):
    destino = request.POST.get("next") or request.GET.get("next") or "/"
    if url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return destino
    return "/"


def ingresar(request):
    """HU01: inicio de sesión con la cuenta de Magneto (adaptador simulado en el Sprint 2)."""
    siguiente = _siguiente(request)
    if request.user.is_authenticated:
        return redirect(siguiente)
    form = IngresoMagnetoForm(request.POST or None)
    error = None
    if request.method == "POST":
        perfil = None
        if form.is_valid():
            perfil = obtener_cliente_magneto().autenticar(form.cleaned_data["email"], form.cleaned_data["clave"])
        if perfil is None:
            error = MENSAJE_CREDENCIALES
        else:
            login(request, vincular_usuario(perfil), backend="django.contrib.auth.backends.ModelBackend")
            return redirect(siguiente)
    return render(request, "acceso_magneto/ingresar.html", {"form": form, "error": error, "next": siguiente})


@login_required
def consumo(request):
    """NF04: consumo de la cuota mensual de tokens."""
    return render(
        request,
        "acceso_magneto/consumo.html",
        {"cuota": ControlCuota().resumen(request.user), "por_agente": consumo_por_agente(request.user)},
    )
