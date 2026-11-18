from django import forms

from core.models import Postulacion


class FiltroEstadoForm(forms.Form):
    estado = forms.ChoiceField(label="Estado", required=False, choices=[("", "Todos"), *Postulacion.Estado.choices])
