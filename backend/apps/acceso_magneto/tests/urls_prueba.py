"""URLs de prueba: las del proyecto + una vista que invoca el grafo (para probar el bloqueo NF04 extremo a extremo)."""
from django.http import HttpResponse
from django.urls import path

from config.urls import urlpatterns as urls_proyecto
from core.servicios.copiloto import CopilotoService


def vista_que_invoca_el_grafo(request):
    CopilotoService().ejecutar(request.user, "prueba_cuota")
    return HttpResponse("grafo invocado")


urlpatterns = [path("prueba/grafo/", vista_que_invoca_el_grafo), *urls_proyecto]
