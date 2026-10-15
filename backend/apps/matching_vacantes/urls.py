from django.urls import path

from . import views

app_name = "matching_vacantes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("recalcular/", views.recalcular, name="recalcular"),
    path("<int:pk>/", views.detalle, name="detalle"),
]
