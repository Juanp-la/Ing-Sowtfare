"""Modelos compartidos (NÚCLEO). Corresponden al diagrama entidad-relación del informe.

Todo modelo que más de una feature necesite vive aquí, con una sola migración inicial.
Los campos con datos personales se guardan cifrados (NF02).
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils import timezone

from .campos import JSONCifradoField, TextoCifradoField

CUOTA_TOKENS_DEFECTO = 20000


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        CANDIDATO = "candidato", "Candidato"
        RECLUTADOR = "reclutador", "Reclutador"
        ADMIN = "admin", "Administrador"

    nombre = models.CharField("nombre", max_length=150, blank=True)
    email = models.EmailField("correo electrónico", unique=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.CANDIDATO)
    magneto_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    cuota_tokens_mes = models.PositiveIntegerField(default=CUOTA_TOKENS_DEFECTO)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.email

    @property
    def nombre_visible(self):
        return self.nombre or self.get_full_name() or self.email.split("@")[0]


def ruta_archivo_hv(instancia, nombre):
    # El nombre en disco es aleatorio (sin datos personales); el original va cifrado en BD.
    return f"hv/{instancia.usuario_id}/{nombre}"


class HojaVida(models.Model):
    class Formato(models.TextChoices):
        PDF = "pdf", "PDF"
        DOCX = "docx", "Word (.docx)"

    class Estado(models.TextChoices):
        CARGADA = "cargada", "Cargada"
        PROCESANDO = "procesando", "Procesando"
        ANALIZADA = "analizada", "Analizada"
        ERROR = "error", "No se pudo leer"

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hojas_vida")
    archivo = models.FileField(upload_to=ruta_archivo_hv, blank=True)
    nombre_archivo = TextoCifradoField(blank=True, default="")
    formato = models.CharField(max_length=10, choices=Formato.choices)
    tamano_bytes = models.PositiveIntegerField(default=0)
    texto_extraido = TextoCifradoField(blank=True, default="")
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.CARGADA)
    fecha_carga = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "hoja de vida"
        verbose_name_plural = "hojas de vida"
        ordering = ["-fecha_carga", "-id"]

    def __str__(self):
        return f"HV {self.pk}"


class PerfilExtraido(models.Model):
    hoja_vida = models.OneToOneField(HojaVida, on_delete=models.CASCADE, related_name="perfil")
    datos = JSONCifradoField(default=dict, blank=True)
    confirmado = models.BooleanField(default=False)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil extraído"
        verbose_name_plural = "perfiles extraídos"

    def __str__(self):
        return f"Perfil de HV {self.hoja_vida_id}"


class Diagnostico(models.Model):
    class Nivel(models.TextChoices):
        BAJO = "bajo", "Bajo"
        POR_MEJORAR = "por_mejorar", "Por mejorar"
        COMPETITIVO = "competitivo", "Competitivo"

    class Estado(models.TextChoices):
        PROCESANDO = "procesando", "Procesando"
        COMPLETADO = "completado", "Completado"
        ERROR = "error", "Error"

    hoja_vida = models.ForeignKey(HojaVida, on_delete=models.CASCADE, related_name="diagnosticos")
    puntaje = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    nivel = models.CharField(max_length=20, choices=Nivel.choices, blank=True)
    explicacion = models.TextField(blank=True)
    criterios = models.JSONField(default=list, blank=True)
    duracion_ms = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROCESANDO)
    mensaje_error = models.CharField(max_length=255, blank=True)
    ejecucion_id = models.CharField(max_length=36, blank=True, db_index=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "diagnóstico"
        verbose_name_plural = "diagnósticos"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Diagnóstico {self.pk} de HV {self.hoja_vida_id}"


class Hallazgo(models.Model):
    class Prioridad(models.TextChoices):
        ALTA = "alta", "Alta"
        MEDIA = "media", "Media"
        BAJA = "baja", "Baja"

    RANGO = {"alta": 1, "media": 2, "baja": 3}

    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE, related_name="hallazgos")
    categoria = models.CharField(max_length=60)
    descripcion = models.TextField()
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.MEDIA)
    rango = models.PositiveSmallIntegerField(default=2, editable=False)
    accion_sugerida = models.TextField(blank=True)

    class Meta:
        verbose_name = "hallazgo"
        verbose_name_plural = "hallazgos"
        ordering = ["rango", "id"]

    def save(self, *args, **kwargs):
        self.rango = self.RANGO.get(self.prioridad, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.prioridad}] {self.categoria}"


class Vacante(models.Model):
    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        REMOTO = "remoto", "Remoto"
        HIBRIDO = "hibrido", "Híbrido"

    magneto_id = models.CharField(max_length=64, unique=True)
    titulo = models.CharField(max_length=200)
    empresa = models.CharField(max_length=200)
    ciudad = models.CharField(max_length=100, db_index=True)
    modalidad = models.CharField(max_length=20, choices=Modalidad.choices, db_index=True)
    salario_min = models.PositiveIntegerField(default=0)
    salario_max = models.PositiveIntegerField(default=0)
    descripcion = models.TextField(blank=True)
    requisitos = models.JSONField(default=list, blank=True)
    activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "vacante"
        verbose_name_plural = "vacantes"
        ordering = ["-fecha_publicacion", "titulo"]

    def __str__(self):
        return f"{self.titulo} - {self.empresa}"


class AjusteVacante(models.Model):
    perfil = models.ForeignKey(PerfilExtraido, on_delete=models.CASCADE, related_name="ajustes")
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name="ajustes")
    score = models.FloatField(default=0)
    cumple = models.JSONField(default=list, blank=True)
    no_cumple = models.JSONField(default=list, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "ajuste de vacante"
        verbose_name_plural = "ajustes de vacantes"
        ordering = ["-score", "id"]
        constraints = [models.UniqueConstraint(fields=["perfil", "vacante"], name="ajuste_unico_perfil_vacante")]

    def __str__(self):
        return f"Ajuste {self.score:.0f} perfil {self.perfil_id} vacante {self.vacante_id}"


class PlanMejora(models.Model):
    hoja_vida = models.ForeignKey(HojaVida, on_delete=models.CASCADE, related_name="planes")
    diagnostico = models.ForeignKey(
        Diagnostico, on_delete=models.CASCADE, related_name="planes", null=True, blank=True
    )
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name="planes", null=True, blank=True)
    acciones = models.JSONField(default=list, blank=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "plan de mejora"
        verbose_name_plural = "planes de mejora"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Plan {self.pk} de HV {self.hoja_vida_id}"


class PreguntaEntrevista(models.Model):
    class Tipo(models.TextChoices):
        TECNICA = "tecnica", "Técnica"
        CONDUCTUAL = "conductual", "Conductual"
        BRECHA = "brecha", "Sobre una brecha"

    hoja_vida = models.ForeignKey(HojaVida, on_delete=models.CASCADE, related_name="preguntas")
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE, related_name="preguntas")
    pregunta = models.TextField()
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.TECNICA)
    brecha = models.CharField(max_length=200, blank=True)
    sugerencia = models.TextField(blank=True)
    orden = models.PositiveSmallIntegerField(default=0)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "pregunta de entrevista"
        verbose_name_plural = "preguntas de entrevista"
        ordering = ["orden", "id"]

    def __str__(self):
        return self.pregunta[:60]


class EjecucionAgente(models.Model):
    """Traza de cada nodo del grafo (NF05) y libro de consumo de tokens (NF04).

    No guarda datos personales: solo el hash de la entrada y un resumen sin valores.
    Si se borra la HV la traza queda (hoja_vida=NULL) para no perder el consumo del mes.
    """

    class Estado(models.TextChoices):
        OK = "ok", "OK"
        ERROR = "error", "Error"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ejecuciones", null=True, blank=True
    )
    hoja_vida = models.ForeignKey(
        HojaVida, on_delete=models.SET_NULL, related_name="ejecuciones", null=True, blank=True
    )
    ejecucion_id = models.CharField(max_length=36, blank=True, db_index=True)
    agente = models.CharField(max_length=60, db_index=True)
    entrada_hash = models.CharField(max_length=64, blank=True)
    salida_resumen = models.TextField(blank=True)
    tokens = models.PositiveIntegerField(default=0)
    duracion_ms = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.OK)
    fecha = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "ejecución de agente"
        verbose_name_plural = "ejecuciones de agentes"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.agente} ({self.estado}) {self.duracion_ms} ms"
