from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cuenta/ingresar/", views.ingresar, name="ingresar"),
    path("cuenta/salir/", views.salir, name="salir"),
]
