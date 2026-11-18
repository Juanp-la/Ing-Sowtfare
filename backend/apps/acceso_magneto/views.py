from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.models import HojaVida
from core.servicios.cuota import ControlCuota

from .clientes import obtener_cliente_magneto
from .forms import IngresoMagnetoForm
from .servicios import consumo_por_agente, importar_hv_magneto, vincular_usuario

MENSAJE_SIN_HV = "No encontramos una hoja de vida en tu perfil de Magneto."

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


def _url_opcional(nombre, *args):
    try:
        return reverse(nombre, args=args)
    except NoReverseMatch:  # la feature de análisis puede no estar instalada en esta rama
        return None


@login_required
def hv_magneto(request):
    """HU04: muestra la HV que el candidato ya tiene en Magneto y si ya la importó."""
    archivo = obtener_cliente_magneto().obtener_hv(request.user.magneto_id)
    importada = None
    if archivo is not None:
        importada = HojaVida.objects.filter(usuario=request.user, origen=HojaVida.Origen.MAGNETO,
                                            huella=archivo.huella).first()
    return render(request, "acceso_magneto/hv_magneto.html", {
        "archivo": archivo, "importada": importada, "mensaje_sin_hv": MENSAJE_SIN_HV,
        "url_cargar": _url_opcional("analisis_hv:cargar"),
    })


@login_required
@require_POST
def importar_hv(request):
    """HU04: usa la HV de Magneto; queda lista para analizar, igual que una carga manual (HU02)."""
    hv, creada = importar_hv_magneto(request.user, obtener_cliente_magneto())
    if hv is None:
        messages.warning(request, MENSAJE_SIN_HV)
        return redirect("acceso_magneto:hv_magneto")
    if creada:
        messages.success(request, f"Usamos la hoja de vida de tu perfil de Magneto: {hv.nombre_archivo}")
    else:
        messages.info(request, "Esa hoja de vida de Magneto ya estaba en el copiloto; abrimos la existente.")
    return redirect(_url_opcional("analisis_hv:detalle", hv.pk) or "acceso_magneto:hv_magneto")
