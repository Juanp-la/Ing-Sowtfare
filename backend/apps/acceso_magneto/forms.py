from django import forms


class IngresoMagnetoForm(forms.Form):
    email = forms.EmailField(label="Correo de Magneto", max_length=254)
    clave = forms.CharField(label="Contraseña", strip=False, widget=forms.PasswordInput)
