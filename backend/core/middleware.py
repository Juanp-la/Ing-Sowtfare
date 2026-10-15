from django.conf import settings
from django.contrib.auth import login
from django.shortcuts import render

from . import plugins
from .datos_demo import EMAIL_DEMO
from .servicios.cuota import CuotaAgotada


class AutoLoginDemoMiddleware:
    """Auto-login de demo: solo con DEBUG=1, DEV_AUTO_LOGIN=1 y sin feature de login propia."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            settings.DEBUG
            and settings.DEV_AUTO_LOGIN
            and not request.user.is_authenticated
            and not request.path.startswith("/admin/")
            and plugins.url_login_externa() is None
        ):
            from .models import Usuario

            usuario = Usuario.objects.filter(email=EMAIL_DEMO, is_active=True).first()
            if usuario:
                login(request, usuario, backend="django.contrib.auth.backends.ModelBackend")
        return self.get_response(request)


class CuotaAgotadaMiddleware:
    """NF04: si una vista intenta invocar el grafo sin cuota, se muestra un aviso (HTTP 429)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, CuotaAgotada):
            return render(request, "core/cuota_agotada.html", {"detalle": str(exception)}, status=429)
        return None
