from django.urls import path

from . import views

app_name = "postulaciones"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("vacante/<int:pk>/", views.nueva, name="nueva"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/retirar/", views.retirar, name="retirar"),
]
