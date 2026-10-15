from django import forms

from core.validadores import MENSAJE_FORMATO_NO_ADMITIDO, validar_archivo_hv


class CargaHVForm(forms.Form):
    archivo = forms.FileField(label="Hoja de vida (PDF o Word, máximo 5 MB)",
                              error_messages={"required": MENSAJE_FORMATO_NO_ADMITIDO,
                                              "empty": MENSAJE_FORMATO_NO_ADMITIDO,
                                              "invalid": MENSAJE_FORMATO_NO_ADMITIDO})

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        self.formato = validar_archivo_hv(archivo)
        return archivo


def _lineas(texto):
    return [linea.strip() for linea in (texto or "").splitlines() if linea.strip()]


def _partes(linea, cantidad):
    partes = [p.strip() for p in linea.split("|")]
    return (partes + [""] * cantidad)[:cantidad]


def _coma(texto):
    return [p.strip() for p in (texto or "").replace("\n", ",").split(",") if p.strip()]


class PerfilForm(forms.Form):
    """HU03: perfil editable. Experiencia y educación van una por línea separando con «|»."""

    nombre = forms.CharField(label="Nombre", required=False, max_length=150)
    email = forms.EmailField(label="Correo", required=False)
    telefono = forms.CharField(label="Teléfono", required=False, max_length=40)
    ciudad = forms.CharField(label="Ciudad", required=False, max_length=100)
    resumen = forms.CharField(label="Perfil profesional", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    experiencia = forms.CharField(label="Experiencia (cargo | empresa | periodo | descripción)", required=False,
                                  widget=forms.Textarea(attrs={"rows": 4}))
    educacion = forms.CharField(label="Educación (título | institución | año)", required=False,
                                widget=forms.Textarea(attrs={"rows": 3}))
    habilidades = forms.CharField(label="Habilidades (separadas por coma)", required=False,
                                  widget=forms.Textarea(attrs={"rows": 2}))
    idiomas = forms.CharField(label="Idiomas (separados por coma)", required=False)

    GRUPOS = (
        ("Datos de contacto", ("nombre", "email", "telefono", "ciudad")),
        ("Perfil y experiencia", ("resumen", "experiencia")),
        ("Educación", ("educacion",)),
        ("Habilidades e idiomas", ("habilidades", "idiomas")),
    )

    @classmethod
    def iniciales(cls, datos):
        contacto = datos.get("contacto", {})
        return {
            "nombre": contacto.get("nombre", ""),
            "email": contacto.get("email", ""),
            "telefono": contacto.get("telefono", ""),
            "ciudad": contacto.get("ciudad", ""),
            "resumen": datos.get("resumen", ""),
            "experiencia": "\n".join(
                " | ".join([e.get("cargo", ""), e.get("empresa", ""), e.get("periodo", ""), e.get("descripcion", "")])
                for e in datos.get("experiencia", [])
            ),
            "educacion": "\n".join(
                " | ".join([e.get("titulo", ""), e.get("institucion", ""), e.get("anio", "")])
                for e in datos.get("educacion", [])
            ),
            "habilidades": ", ".join(datos.get("habilidades", [])),
            "idiomas": ", ".join(datos.get("idiomas", [])),
        }

    def a_perfil(self):
        d = self.cleaned_data
        experiencia = []
        for linea in _lineas(d["experiencia"]):
            cargo, empresa, periodo, descripcion = _partes(linea, 4)
            experiencia.append({"cargo": cargo, "empresa": empresa, "periodo": periodo, "descripcion": descripcion})
        educacion = []
        for linea in _lineas(d["educacion"]):
            titulo, institucion, anio = _partes(linea, 3)
            educacion.append({"titulo": titulo, "institucion": institucion, "anio": anio})
        return {
            "contacto": {"nombre": d["nombre"], "email": d["email"], "telefono": d["telefono"], "ciudad": d["ciudad"]},
            "resumen": d["resumen"].strip(),
            "experiencia": experiencia,
            "educacion": educacion,
            "habilidades": _coma(d["habilidades"]),
            "idiomas": _coma(d["idiomas"]),
        }

    def grupos(self):
        """Campos agrupados; los vacíos se marcan para resaltarlos."""
        resultado = []
        for titulo, nombres in self.GRUPOS:
            campos = []
            for nombre in nombres:
                campo = self[nombre]
                valor = campo.value() if self.is_bound else self.initial.get(nombre, "")
                campos.append({"campo": campo, "vacio": not str(valor or "").strip()})
            resultado.append({"titulo": titulo, "campos": campos})
        return resultado
