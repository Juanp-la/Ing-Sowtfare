from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import HojaVida


@receiver(post_delete, sender=HojaVida)
def borrar_archivo_hv(sender, instance, **kwargs):
    """NF02: al borrar la HV también se borra el archivo cifrado del disco."""
    if instance.archivo:
        instance.archivo.delete(save=False)
