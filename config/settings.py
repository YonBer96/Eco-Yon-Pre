"""
Configuración principal del proyecto Eco-Yon.

Aquí se definen:
- apps activas
- base de datos
- autenticación
- API
- archivos estáticos y media
- JWT
"""

from pathlib import Path
from datetime import timedelta

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# =========================
# CONFIGURACIÓN BÁSICA
# =========================

# Clave secreta del proyecto (no debe subirse a producción tal cual)
SECRET_KEY = 'django-insecure-517y0s7ljbjujoj37#a2k1&em=+q2z@!cyi2^4b*8be(n3b#vi'

# Modo desarrollo (en producción debe ser False)
DEBUG = True

# Dominios permitidos (vacío solo en desarrollo)
ALLOWED_HOSTS = []


# =========================
# APLICACIONES ACTIVAS
# =========================

INSTALLED_APPS = [
    # Apps base de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías externas
    "rest_framework",
    "corsheaders",
    "rest_framework_simplejwt.token_blacklist",

    # Apps del proyecto
    "accounts",
    "catalog",
    "dashboard",
    "pages",
    "orders",
]


# =========================
# MIDDLEWARES
# =========================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Permite peticiones desde el frontend
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =========================
# CONFIGURACIÓN DE URLs Y TEMPLATES
# =========================

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Carpeta global de templates
        'APP_DIRS': True,                  # Permite templates dentro de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# =========================
# BASE DE DATOS
# =========================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# =========================
# VALIDACIÓN DE CONTRASEÑAS
# =========================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =========================
# IDIOMA Y ZONA HORARIA
# =========================

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"

USE_I18N = True
USE_TZ = True


# =========================
# ARCHIVOS ESTÁTICOS
# =========================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]


# =========================
# DJANGO REST FRAMEWORK
# =========================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}


# =========================
# CORS
# =========================

# Permite llamadas a la API desde cualquier origen (solo desarrollo)
CORS_ALLOW_ALL_ORIGINS = True


# =========================
# EMAIL Y FACTURAS
# =========================

# Emails se muestran en consola
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DEFAULT_FROM_EMAIL = "tienda@fruteria.com"
SHOP_EMAIL = "dueno@fruteria.com"

# Logo usado en facturas y albaranes
INVOICE_LOGO_PATH = BASE_DIR / "static" / "img" / "logo-ecoyon.png"


# =========================
# ARCHIVOS SUBIDOS (IMÁGENES)
# =========================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================
# CONFIGURACIÓN GENERAL
# =========================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================
# JWT (AUTENTICACIÓN)
# =========================

SIMPLE_JWT = {
    # Tiempo de vida del access token
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),

    # Tiempo de vida del refresh token
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),

    # Rotar refresh tokens al renovarlos
    "ROTATE_REFRESH_TOKENS": True,

    # Invalidar refresh tokens antiguos
    "BLACKLIST_AFTER_ROTATION": True,

    # Prefijo en el header Authorization
    "AUTH_HEADER_TYPES": ("Bearer",),
}
