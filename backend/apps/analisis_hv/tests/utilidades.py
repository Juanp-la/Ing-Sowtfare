from core.datos_demo import TEXTO_HV_DEMO
from core.models import HojaVida
from core.pruebas.fabricas import archivo_subido, docx_bytes, pdf_bytes


def subir(cliente, nombre="hv_sintetica.pdf", contenido=None):
    if contenido is None:
        contenido = docx_bytes(TEXTO_HV_DEMO) if nombre.endswith(".docx") else pdf_bytes(TEXTO_HV_DEMO)
    return cliente.post("/hv/cargar/", {"archivo": archivo_subido(nombre, contenido)})


def subir_y_analizar(cliente, nombre="hv_sintetica.pdf", contenido=None):
    subir(cliente, nombre, contenido)
    hv = HojaVida.objects.latest("id")
    return hv, cliente.post(f"/hv/{hv.pk}/analizar/", follow=True)
