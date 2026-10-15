"""Factories con datos sintéticos (sin dependencias extra)."""
import copy
import io
import itertools
import secrets

from django.core.files.uploadedfile import SimpleUploadedFile

from core.datos_demo import PERFIL_DEMO, TEXTO_HV_DEMO, VACANTES_DEMO

_secuencia = itertools.count(1)


def crear_usuario(email=None, clave=None, **extra):
    from core.models import Usuario

    n = next(_secuencia)
    email = email or f"candidato{n}@copiloto.test"
    extra.setdefault("username", f"usuario{n}")
    extra.setdefault("nombre", f"Candidato Sintético {n}")
    return Usuario.objects.create_user(email=email, password=clave or secrets.token_urlsafe(12), **extra)


def crear_hv(usuario, texto=TEXTO_HV_DEMO, perfil=PERFIL_DEMO, estado=None, confirmado=True, con_archivo=False):
    from core.models import HojaVida, PerfilExtraido
    from core.servicios.archivos import guardar_archivo_hv

    hv = HojaVida(
        usuario=usuario,
        nombre_archivo="hv_sintetica.pdf",
        formato=HojaVida.Formato.PDF,
        texto_extraido=texto,
        estado=estado or (HojaVida.Estado.ANALIZADA if perfil is not None else HojaVida.Estado.CARGADA),
    )
    if con_archivo:
        guardar_archivo_hv(hv, pdf_bytes(texto or "HV"))
    hv.save()
    if perfil is not None:
        PerfilExtraido.objects.create(hoja_vida=hv, datos=copy.deepcopy(perfil), confirmado=confirmado)
    return hv


def crear_vacante(**datos):
    from core.models import Vacante

    n = next(_secuencia)
    base = {
        "magneto_id": f"MAG-T-{n:04d}",
        "titulo": f"Vacante sintética {n}",
        "empresa": "Empresa Ficticia",
        "ciudad": "Medellín",
        "modalidad": Vacante.Modalidad.PRESENCIAL,
        "salario_min": 2000000,
        "salario_max": 3000000,
        "requisitos": [{"tipo": "habilidad", "valor": "SQL", "obligatorio": True}],
    }
    base.update(datos)
    return Vacante.objects.create(**base)


def crear_vacantes_demo():
    from core.models import Vacante

    return [Vacante.objects.create(**copy.deepcopy(d)) for d in VACANTES_DEMO]


def pdf_bytes(texto):
    import pymupdf

    documento = pymupdf.open()
    pagina = documento.new_page()
    y = 72
    for linea in texto.splitlines() or [""]:
        pagina.insert_text((50, y), linea, fontsize=10)
        y += 14
        if y > 780:
            pagina = documento.new_page()
            y = 72
    contenido = documento.tobytes()
    documento.close()
    return contenido


def docx_bytes(texto):
    from docx import Document

    documento = Document()
    for linea in texto.splitlines():
        documento.add_paragraph(linea)
    salida = io.BytesIO()
    documento.save(salida)
    return salida.getvalue()


def archivo_subido(nombre, contenido, tipo="application/octet-stream"):
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)
