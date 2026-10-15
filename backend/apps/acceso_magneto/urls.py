from django.urls import path

from . import views

app_name = "acceso_magneto"

urlpatterns = [
    path("ingresar/", views.ingresar, name="ingresar"),
    path("consumo/", views.consumo, name="consumo"),
]
