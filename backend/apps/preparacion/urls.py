from django.urls import path

from . import views

app_name = "preparacion"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("vacante/<int:pk>/", views.vacante, name="vacante"),
    path("vacante/<int:pk>/generar/", views.generar, name="generar"),
]
