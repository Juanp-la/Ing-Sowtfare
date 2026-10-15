"""URLs raíz (NÚCLEO). Cada feature se monta con el prefijo_url de su AppConfig."""
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from core import plugins

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]

for config in plugins.apps_feature():
    urlpatterns.append(path(plugins.prefijo_url(config), include(f"{config.name}.urls")))

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
