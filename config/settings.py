import os
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------
# Helpers de entorno
# -----------------------------
def env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [x.strip() for x in os.getenv(name, default).split(",") if x.strip()]


# -----------------------------
# Básicos
# -----------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret")
DEBUG = env_bool("DEBUG", "1")  # en local: DEBUG=1; en prod: DEBUG=0

# ALLOWED_HOSTS:
# - Prod: pon el dominio exacto en la env ALLOWED_HOSTS (sin https), ej: "web-production-d48a.up.railway.app"
# - Dev: por defecto permite localhost
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1") if DEBUG else env_list("ALLOWED_HOSTS")

# CSRF_TRUSTED_ORIGINS:
# - Prod: **debe** contener orígenes completos con https, ej: "https://web-production-d48a.up.railway.app"
# - Dev: por defecto habilita http://localhost:8000 y http://127.0.0.1:8000
_csrf_env = env_list("CSRF_TRUSTED_ORIGINS")
if _csrf_env:
    CSRF_TRUSTED_ORIGINS = _csrf_env
else:
    CSRF_TRUSTED_ORIGINS = (
        ["http://localhost:8000", "http://127.0.0.1:8000"] if DEBUG
        else [f"https://{h}" for h in ALLOWED_HOSTS if h and h not in {"localhost", "127.0.0.1", "*"}]
    )

# -----------------------------
# Apps
# -----------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # terceros
    "rest_framework",
    "corsheaders",

    # locales
    "matches",
    "accounts",
]

# -----------------------------
# Middleware
# -----------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # CORS antes de CommonMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# -----------------------------
# Base de Datos
# -----------------------------
# Producción (Railway): define DATABASE_URL (la referencia ${{Postgres.DATABASE_URL}})
# Local: por defecto SQLite; si pones DATABASE_URL en tu .env, lo usará
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    db_cfg = dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
    db_cfg.setdefault("OPTIONS", {})
    # 🔁 pon la sesión de Postgres en UTC (o elimina esta línea)
    db_cfg["OPTIONS"]["options"] = "-c timezone=UTC"
    DATABASES = {"default": db_cfg}

# -----------------------------
# Usuario / DRF / JWT
# -----------------------------
AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.utils.authentication.DeviceTokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DATE_INPUT_FORMATS": ["%d/%m/%Y", "%Y-%m-%d"],
    "DATE_FORMAT": "%d/%m/%Y",
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# -----------------------------
# Archivos estáticos
# -----------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}
}

# -----------------------------
# CORS
# -----------------------------
CORS_ALLOW_ALL_ORIGINS = env_bool("CORS_ALLOW_ALL_ORIGINS", "0")
# Si no quieres abrir all, especifica orígenes explícitos (URLs completas)
CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS") if not CORS_ALLOW_ALL_ORIGINS else []

# -----------------------------
# Seguridad (proxy + cookies)
# -----------------------------
# Para HTTPS detrás de Railway
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    # (Opcional) Forzar HTTPS si tienes dominio con SSL
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", "1")

# -----------------------------
# Localización
# -----------------------------
LANGUAGE_CODE = "es"
USE_I18N = True
USE_TZ = True
TIME_ZONE = "UTC"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
