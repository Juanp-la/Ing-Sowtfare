from urllib.parse import urlencode

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import plugins


@login_required
def inicio(request):
    return render(request, "core/inicio.html")


def ingresar(request):
    """Si una feature declara url_login (p. ej. Magneto) se delega en ella; si no, login mínimo de Django."""
    externa = plugins.url_login_externa()
    if externa:
        siguiente = request.GET.get("next", "")
        if siguiente and url_has_allowed_host_and_scheme(siguiente, allowed_hosts={request.get_host()}):
            externa = f"{externa}?{urlencode({'next': siguiente})}"
        return redirect(externa)
    return LoginView.as_view(template_name="core/ingresar.html", redirect_authenticated_user=True)(request)


@require_POST
def salir(request):
    logout(request)
    return redirect("core:ingresar")
