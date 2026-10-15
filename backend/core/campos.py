"""Campos de modelo cifrados con Fernet (NF02). En la BD solo queda el texto cifrado.

Limitación conocida: al ser cifrado no determinista, no se puede filtrar por estos campos.
"""
import json

from django.db import models

from .servicios import cifrado


class TextoCifradoField(models.TextField):
    description = "Texto cifrado (Fernet)"

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if value in (None, ""):
            return value
        return cifrado.cifrar(value)

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return value
        texto = cifrado.descifrar(value)
        return "" if texto is None else texto


class JSONCifradoField(models.TextField):
    description = "JSON cifrado (Fernet)"

    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except ValueError:
                return value
        return value

    def get_prep_value(self, value):
        if value is None:
            return None
        return cifrado.cifrar(json.dumps(value, ensure_ascii=False))

    def from_db_value(self, value, expression, connection):
        if value in (None, ""):
            return {}
        texto = cifrado.descifrar(value)
        if texto is None:
            return {}
        return json.loads(texto)

    def value_to_string(self, obj):
        return json.dumps(self.value_from_object(obj), ensure_ascii=False)
