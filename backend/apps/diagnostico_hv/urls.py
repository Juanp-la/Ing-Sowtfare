from django.urls import path

from . import views

app_name = "diagnostico_hv"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("hv/<int:hv_pk>/diagnosticar/", views.diagnosticar, name="diagnosticar"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/estado.json", views.estado, name="estado"),
    path("trazabilidad/", views.trazabilidad, name="trazabilidad"),
]
