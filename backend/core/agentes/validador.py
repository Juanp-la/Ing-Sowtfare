"""ValidadorVeracidad (NF03): ningún dato generado puede salir de la nada.

Compara cada texto generado contra el texto original de la HV. Un valor se acepta si
aparece literal (normalizado) o si al menos el 80 % de sus palabras significativas están
en la HV y todos sus números (años, cifras) también. Lo demás se rechaza.
"""
from ..dominio.texto import normalizar, palabras
from .base import AgenteBase

UMBRAL_COBERTURA = 0.8


class ValidadorVeracidad:
    def __init__(self, umbral=UMBRAL_COBERTURA):
        self.umbral = umbral

    def soportado(self, valor, original_normalizado, palabras_original):
        valor_n = normalizar(valor)
        if not valor_n or valor_n in original_normalizado:
            return True
        tokens = [t for t in palabras(valor) if len(t) >= 4 or t.isdigit()]
        if not tokens:
            return valor_n in original_normalizado
        if any(t.isdigit() and t not in palabras_original for t in tokens):
            return False
        presentes = sum(1 for t in tokens if t in palabras_original)
        return presentes / len(tokens) >= self.umbral

    def _contexto(self, original):
        return normalizar(original), set(palabras(original))

    def _hojas(self, valor):
        if isinstance(valor, dict):
            for v in valor.values():
                yield from self._hojas(v)
        elif isinstance(valor, (list, tuple)):
            for v in valor:
                yield from self._hojas(v)
        elif isinstance(valor, str) and valor.strip():
            yield valor

    def verificar(self, original, generado):
        """Devuelve la lista de valores inventados (no soportados por el original)."""
        contexto = self._contexto(original)
        inventados = []
        for hoja in self._hojas(generado):
            if not self.soportado(hoja, *contexto) and hoja not in inventados:
                inventados.append(hoja)
        return inventados

    def depurar(self, original, generado):
        """Quita lo inventado: campos sueltos quedan vacíos y se descarta la entrada de lista completa."""
        contexto = self._contexto(original)

        def ok(texto):
            return self.soportado(texto, *contexto)

        def limpiar(valor):
            if isinstance(valor, dict):
                return {k: limpiar(v) for k, v in valor.items()}
            if isinstance(valor, list):
                resultado = []
                for item in valor:
                    if isinstance(item, (dict, list)):
                        if all(ok(h) for h in self._hojas(item)):
                            resultado.append(item)
                    elif isinstance(item, str):
                        if ok(item):
                            resultado.append(item)
                    else:
                        resultado.append(item)
                return resultado
            if isinstance(valor, str):
                return valor if (not valor.strip() or ok(valor)) else ""
            return valor

        return limpiar(generado)


class NodoValidador(AgenteBase):
    """Nodo del grafo que aplica ValidadorVeracidad a la salida de otro agente."""

    nombre = "validador"
    campo = "perfil"
    campo_original = "texto_hv"

    def __init__(self, llm=None, trazador=None, validador=None):
        super().__init__(llm=llm, trazador=trazador)
        self.validador = validador or ValidadorVeracidad()

    def ejecutar(self, estado):
        original = estado.get(self.campo_original, "")
        generado = estado.get(self.campo) or {}
        inventados = self.validador.verificar(original, generado)
        return {
            self.campo: self.validador.depurar(original, generado) if inventados else generado,
            "validacion": {"ok": not inventados, "rechazados": inventados, "campo": self.campo},
        }
