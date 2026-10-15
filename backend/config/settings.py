"""Configuración de Django (NÚCLEO).

Las features se descubren solas: cada carpeta backend/apps/<app>/ con un apps.py
se agrega a INSTALLED_APPS. Agregar una feature no requiere editar este archivo.
"""
import os
import secrets
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
RAIZ_REPO = BASE_DIR.parent
FRONTEND_DIR = RAIZ_REPO / "frontend"


def _cargar_env(ruta):
    """Carga KEY=VALOR desde un .env local sin dependencias; no pisa variables ya definidas."""
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def _bool(nombre, defecto="0"):
    return os.environ.get(nombre, defecto).strip().lower() in {"1", "true", "si", "yes", "on"}


_cargar_env(RAIZ_REPO / ".env")

DEBUG = _bool("DJANGO_DEBUG", "1")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatoria cuando DJANGO_DEBUG=0.")
    SECRET_KEY = secrets.token_urlsafe(50)  # efímera, solo desarrollo

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver").split(",")
    if h.strip()
]

# --- Descubrimiento de features (plug-in) ---
APPS_DIR = BASE_DIR / "apps"
FEATURE_APPS = sorted(f"apps.{ruta.parent.name}" for ruta in APPS_DIR.glob("*/apps.py"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    *FEATURE_APPS,
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "core.middleware.AutoLoginDemoMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.CuotaAgotadaMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.copiloto",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# SQLite por defecto; PostgreSQL 16 con DATABASE_URL (docker-compose).
# Un DATABASE_URL vacío (como en .env.example) cuenta como no definido.
DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get("DATABASE_URL") or f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}", conn_max_age=60
    )
}

AUTH_USER_MODEL = "core.Usuario"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "core:ingresar"
LOGIN_REDIRECT_URL = "core:inicio"
LOGOUT_REDIRECT_URL = "core:ingresar"

LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [FRONTEND_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Las HV se guardan cifradas en MEDIA_ROOT y nunca se sirven por URL.
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Subida de HV (HU02 / OWASP) ---
HV_TAMANO_MAXIMO = 5 * 1024 * 1024
HV_EXTENSIONES = (".pdf", ".docx")
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024

# --- Seguridad mínima ---
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = _bool("DJANGO_SSL_REDIRECT", "1")
    SECURE_HSTS_SECONDS = 3600

# --- Copiloto ---
CAMPOS_CIFRADO_KEY = os.environ.get("CAMPOS_CIFRADO_KEY", "")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock").strip().lower() or "mock"
LLM_MODEL = os.environ.get("LLM_MODEL", "")
LLM_CACHE = _bool("LLM_CACHE", "1")
CUOTA_TOKENS_DEFECTO = int(os.environ.get("CUOTA_TOKENS_DEFECTO", "20000"))
COPILOTO_TAREAS_ASINCRONAS = _bool("COPILOTO_TAREAS_ASINCRONAS", "1")
MAGNETO_CLIENT = os.environ.get("MAGNETO_CLIENT", "mock")
DEV_AUTO_LOGIN = _bool("DEV_AUTO_LOGIN", "0")

# --- Logs sin datos personales ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"sin_pii": {"()": "core.registro_logs.FiltroSinPII"}},
    "handlers": {"consola": {"class": "logging.StreamHandler", "filters": ["sin_pii"]}},
    "root": {"handlers": ["consola"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}
