"""manage.py seed_demo: usuario demo, HV sintética y vacantes sintéticas.

La clave del usuario demo se genera al azar, se imprime en consola y no se guarda en ningún archivo.
"""
import secrets

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from core.datos_demo import (
    CANDIDATOS_POSTULADOS_DEMO,
    EMAIL_DEMO,
    EMAIL_RECLUTADOR_DEMO,
    MAGNETO_ID_DEMO,
    MAGNETO_ID_RECLUTADOR_DEMO,
    NOMBRE_DEMO,
    NOMBRE_RECLUTADOR_DEMO,
    PERFIL_DEMO,
    TEXTO_HV_DEMO,
    VACANTES_DEMO,
)
from core.dominio.texto import texto_perfil
from core.models import HojaVida, PerfilExtraido, Postulacion, Usuario, Vacante
from core.pruebas.fabricas import pdf_bytes
from core.servicios.archivos import guardar_archivo_hv


class Command(BaseCommand):
    help = "Carga datos sintéticos de demostración (idempotente)."

    def add_arguments(self, parser):
        parser.add_argument("--sin-hv", action="store_true", help="No crear la HV demo.")

    @transaction.atomic
    def handle(self, *args, **opciones):
        clave = secrets.token_urlsafe(9)
        usuario, creado = Usuario.objects.get_or_create(
            email=EMAIL_DEMO,
            defaults={"username": "demo", "nombre": NOMBRE_DEMO, "magneto_id": MAGNETO_ID_DEMO},
        )
        usuario.nombre = NOMBRE_DEMO
        usuario.magneto_id = MAGNETO_ID_DEMO
        usuario.cuota_tokens_mes = settings.CUOTA_TOKENS_DEFECTO
        usuario.set_password(clave)
        usuario.save()

        clave_reclutador = secrets.token_urlsafe(9)
        reclutador, _ = Usuario.objects.get_or_create(
            email=EMAIL_RECLUTADOR_DEMO,
            defaults={"username": "reclutador-demo", "nombre": NOMBRE_RECLUTADOR_DEMO,
                      "magneto_id": MAGNETO_ID_RECLUTADOR_DEMO, "rol": Usuario.Rol.RECLUTADOR},
        )
        reclutador.rol = Usuario.Rol.RECLUTADOR
        reclutador.set_password(clave_reclutador)
        reclutador.save()

        for datos in VACANTES_DEMO:
            Vacante.objects.update_or_create(magneto_id=datos["magneto_id"], defaults={**datos, "reclutador": reclutador})

        if not opciones["sin_hv"] and not usuario.hojas_vida.exists():
            hv = HojaVida(
                usuario=usuario,
                nombre_archivo="hv_demo_sintetica.pdf",
                formato=HojaVida.Formato.PDF,
                texto_extraido=TEXTO_HV_DEMO,
                estado=HojaVida.Estado.ANALIZADA,
            )
            guardar_archivo_hv(hv, pdf_bytes(TEXTO_HV_DEMO))
            hv.save()
            PerfilExtraido.objects.create(hoja_vida=hv, datos=PERFIL_DEMO, confirmado=True)

        postuladas = self._postulaciones_demo()

        self.stdout.write(self.style.SUCCESS(f"Usuario demo {'creado' if creado else 'actualizado'}."))
        self.stdout.write(f"  correo: {EMAIL_DEMO}")
        self.stdout.write(f"  clave (nueva en cada ejecución, no se guarda): {clave}")
        self.stdout.write(self.style.SUCCESS("Reclutador demo (Sprint 3):"))
        self.stdout.write(f"  correo: {EMAIL_RECLUTADOR_DEMO}")
        self.stdout.write(f"  clave (nueva en cada ejecución, no se guarda): {clave_reclutador}")
        self.stdout.write(f"  vacantes sintéticas: {Vacante.objects.count()}")
        self.stdout.write(f"  postulaciones sintéticas nuevas: {postuladas}")
        if not settings.CAMPOS_CIFRADO_KEY:
            self.stdout.write(self.style.WARNING(
                "CAMPOS_CIFRADO_KEY no definida: la HV demo quedó cifrada con una clave efímera y no se "
                "podrá leer tras reiniciar. Defina la variable en .env y vuelva a ejecutar seed_demo."
            ))

    def _postulaciones_demo(self):
        """Candidatos sintéticos ya postulados para que el reclutador tenga a quién ordenar (HU19)."""
        from apps.postulaciones.servicios import YaPostulado, postular

        creadas = 0
        for datos in CANDIDATOS_POSTULADOS_DEMO:
            candidato, _ = Usuario.objects.get_or_create(
                email=datos["email"],
                defaults={"username": datos["magneto_id"].lower(), "nombre": datos["nombre"],
                          "magneto_id": datos["magneto_id"]},
            )
            if not candidato.has_usable_password():
                candidato.set_unusable_password()
            candidato.save()
            hv = candidato.hojas_vida.first()
            if hv is None:
                texto = texto_perfil(datos["perfil"])
                hv = HojaVida.objects.create(usuario=candidato, nombre_archivo="hv_sintetica.pdf",
                                             formato=HojaVida.Formato.PDF, texto_extraido=texto,
                                             estado=HojaVida.Estado.ANALIZADA)
                PerfilExtraido.objects.create(hoja_vida=hv, datos=datos["perfil"], confirmado=True)
            for magneto_id in datos["vacantes"]:
                vacante = Vacante.objects.get(magneto_id=magneto_id)
                if Postulacion.objects.filter(usuario=candidato, vacante=vacante).exists():
                    continue
                try:
                    postular(candidato, vacante, perfil=hv.perfil)
                    creadas += 1
                except YaPostulado:
                    continue
        return creadas
