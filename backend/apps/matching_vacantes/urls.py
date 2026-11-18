from django.urls import path

from . import views

app_name = "matching_vacantes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("recalcular/", views.recalcular, name="recalcular"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("alertas/", views.alertas, name="alertas"),
    path("alertas/leidas/", views.marcar_todas, name="marcar_todas"),
    path("alertas/<int:pk>/leida/", views.marcar_alerta, name="marcar_alerta"),
]
