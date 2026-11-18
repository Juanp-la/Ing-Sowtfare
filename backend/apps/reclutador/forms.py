from django import forms

from core.models import Postulacion


class DecisionForm(forms.Form):
    decision = forms.ChoiceField(
        label="Decisión", widget=forms.RadioSelect,
        choices=[(Postulacion.Estado.APTO, "Apto"), (Postulacion.Estado.NO_APTO, "No apto")],
    )
    comentario = forms.CharField(label="Comentario para el candidato", required=False, max_length=1000,
                                 widget=forms.Textarea(attrs={"rows": 3}))

    def clean(self):
        datos = super().clean()
        if datos.get("decision") == Postulacion.Estado.NO_APTO and not (datos.get("comentario") or "").strip():
            self.add_error("comentario", "Explica al candidato por qué no es apto: es su retroalimentación.")
        return datos


class FiltroCandidatosForm(forms.Form):
    estado = forms.ChoiceField(label="Estado", required=False, choices=[("", "Todos"), *Postulacion.Estado.choices])
