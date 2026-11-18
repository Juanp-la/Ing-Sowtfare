from django.urls import path

from . import views

app_name = "reclutador"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("vacante/<int:pk>/", views.candidatos, name="candidatos"),
    path("postulacion/<int:pk>/", views.evaluar, name="evaluar"),
]
