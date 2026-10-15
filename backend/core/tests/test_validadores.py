import io
import zipfile

import pytest
from django.core.exceptions import ValidationError

from core.pruebas.fabricas import archivo_subido, docx_bytes, pdf_bytes
from core.validadores import MENSAJE_FORMATO_NO_ADMITIDO, validar_archivo_hv


def test_acepta_pdf_y_docx_reales():
    assert validar_archivo_hv(archivo_subido("hv.pdf", pdf_bytes("Hola"))) == "pdf"
    assert validar_archivo_hv(archivo_subido("HV.DOCX", docx_bytes("Hola"))) == "docx"


@pytest.mark.parametrize(
    "nombre,contenido",
    [
        ("hv.txt", b"texto plano"),
        ("hv.doc", b"\xd0\xcf\x11\xe0 binario viejo"),
        ("hv.pdf", b""),
        ("hv.pdf", b"MZ ejecutable disfrazado"),
        ("hv.docx", b"PK\x03\x04 no es zip"),
        ("sin_extension", b"%PDF-1.4"),
    ],
)
def test_rechaza_otros_formatos_y_firmas_falsas(nombre, contenido):
    with pytest.raises(ValidationError) as error:
        validar_archivo_hv(archivo_subido(nombre, contenido))
    assert error.value.messages == [MENSAJE_FORMATO_NO_ADMITIDO]


def test_rechaza_zip_que_no_es_word():
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w") as zf:
        zf.writestr("otra/cosa.xml", "<x/>")
    with pytest.raises(ValidationError):
        validar_archivo_hv(archivo_subido("hv.docx", salida.getvalue()))


def test_rechaza_mas_de_5_mb(settings):
    contenido = b"%PDF-1.4" + b"0" * (settings.HV_TAMANO_MAXIMO + 1)
    with pytest.raises(ValidationError):
        validar_archivo_hv(archivo_subido("grande.pdf", contenido))
