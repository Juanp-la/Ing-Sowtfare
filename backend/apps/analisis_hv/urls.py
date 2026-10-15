from django.urls import path

from . import views

app_name = "analisis_hv"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("cargar/", views.cargar, name="cargar"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/analizar/", views.analizar, name="analizar"),
    path("<int:pk>/perfil/", views.perfil, name="perfil"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
