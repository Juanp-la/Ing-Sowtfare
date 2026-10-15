"""Filtro de logs que enmascara correos y teléfonos (logs sin PII)."""
import logging
import re

_CORREO = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_TELEFONO = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def enmascarar(texto):
    return _TELEFONO.sub("[telefono]", _CORREO.sub("[correo]", texto))


class FiltroSinPII(logging.Filter):
    def filter(self, record):
        record.msg = enmascarar(record.getMessage())
        record.args = None
        return True
