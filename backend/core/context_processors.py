from . import plugins


def copiloto(request):
    return {
        "nombre_app": "Magneto Copiloto",
        "menu_copiloto": plugins.menu(getattr(request, "user", None)),
        "fragmentos_navbar": plugins.fragmentos_navbar(),
    }
