from django.urls import path

from . import views

app_name = "adaptacion_hv"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("vacante/<int:pk>/", views.vacante, name="vacante"),
    path("vacante/<int:pk>/generar/", views.generar, name="generar"),
    path("<int:pk>/", views.comparar, name="comparar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    path("<int:pk>/descargar/", views.descargar, name="descargar"),
]
