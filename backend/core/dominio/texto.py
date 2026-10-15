import re
import unicodedata

_ESPACIOS = re.compile(r"\s+")
_PALABRA = re.compile(r"[a-z0-9+#]+")


def normalizar(texto):
    """Minúsculas, sin tildes y con espacios simples."""
    texto = unicodedata.normalize("NFKD", str(texto or ""))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return _ESPACIOS.sub(" ", texto.lower()).strip()


def palabras(texto):
    return _PALABRA.findall(normalizar(texto))


def texto_perfil(perfil):
    """Aplana el perfil (dict/list anidados) a un solo texto."""
    partes = []

    def recorrer(valor):
        if isinstance(valor, dict):
            for v in valor.values():
                recorrer(v)
        elif isinstance(valor, (list, tuple)):
            for v in valor:
                recorrer(v)
        elif valor not in (None, ""):
            partes.append(str(valor))

    recorrer(perfil or {})
    return " ".join(partes)
