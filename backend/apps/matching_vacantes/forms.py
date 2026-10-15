from django import forms

from core.models import Vacante


class FiltroVacantesForm(forms.Form):
    ciudad = forms.ChoiceField(label="Ciudad", required=False)
    modalidad = forms.ChoiceField(label="Modalidad", required=False,
                                  choices=[("", "Todas"), *Vacante.Modalidad.choices])
    salario_min = forms.IntegerField(label="Salario desde", required=False, min_value=0)
    salario_max = forms.IntegerField(label="Salario hasta", required=False, min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ciudades = (Vacante.objects.filter(activa=True).order_by("ciudad")
                    .values_list("ciudad", flat=True).distinct())
        self.fields["ciudad"].choices = [("", "Todas"), *[(c, c) for c in ciudades]]

    def clean(self):
        datos = super().clean()
        minimo, maximo = datos.get("salario_min"), datos.get("salario_max")
        if minimo is not None and maximo is not None and minimo > maximo:
            raise forms.ValidationError("El salario «desde» no puede ser mayor que el salario «hasta».")
        return datos
