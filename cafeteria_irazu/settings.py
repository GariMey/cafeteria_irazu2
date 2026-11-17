import os
from pathlib import Path

import dj_database_url
from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# VARIABLES DE ENTORNO
# Todas las claves vienen del entorno (.env en local, "Environment" en Render);
# ninguna se escribe en el código.

SECRET_KEY = config('SECRET_KEY', default='django-insecure-cafeteria-irazu-cartago-costa-rica-2024')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')
CSRF_TRUSTED_ORIGINS = [
    'https://cafeteria-irazu2.onrender.com',
    'https://cafeteria-irazu2-4tub.onrender.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Render define RENDER_EXTERNAL_HOSTNAME con la dirección del servicio
# (ej. cafeteria-irazu.onrender.com); se permite automáticamente.
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    if '*' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

if not DEBUG:
    # Render entrega HTTPS a través de un proxy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cafeteria',
    'cart',
    'bookings',
    'newsletter',
    'payments',
    'dashboard',
    'panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cafeteria_irazu.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart',
            ],
        },
    },
]

WSGI_APPLICATION = 'cafeteria_irazu.wsgi.application'

# BASE DE DATOS: PostgreSQL en Render (DATABASE_URL) o SQLite en local
# Se limpian espacios y comillas que suelen colarse al copiar la URL.
DATABASE_URL = config('DATABASE_URL', default='').strip().strip('"\'').strip()
if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
elif not DATABASE_URL.split('://', 1)[0].isalpha():
    raise ImproperlyConfigured(
        "DATABASE_URL no es válida: debe ser la URL completa de la base de datos, "
        "que empieza con postgresql:// (en Render: Internal Database URL)."
    )
DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es-cr'
TIME_ZONE = 'America/Costa_Rica'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ALMACENAMIENTO DE ARCHIVOS
# Las imágenes subidas (productos, galería, experiencia) van a Cloudinary si hay
# credenciales; si no, a la carpeta media/ local. Se aceptan dos formas:
#   CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
#   o CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET
# (Django 6 usa STORAGES; DEFAULT_FILE_STORAGE y STATICFILES_STORAGE ya no existen.)
CLOUDINARY_URL = config('CLOUDINARY_URL', default='')
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

if CLOUDINARY_URL or all(CLOUDINARY_STORAGE.values()):
    if CLOUDINARY_URL:
        # La librería de Cloudinary lee esta variable desde el entorno del sistema
        os.environ.setdefault('CLOUDINARY_URL', CLOUDINARY_URL)
        CLOUDINARY_STORAGE = {}
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
    STORAGES['default'] = {'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage'}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# PEDIDOS
IVA_RATE = '0.13'        # IVA de Costa Rica (13 %)
DELIVERY_FEE = '1500'    # Costo de envío a domicilio en colones
ORDER_CONTACT_RETENTION_DAYS = 7  # Respaldo: borra el contacto de pedidos abiertos más tiempo

# MÉTODOS DE PAGO
SINPE_NUMBER = config('SINPE_NUMBER', default='6353-1551')         # Número que recibe los SINPE
SINPE_HOLDER = config('SINPE_HOLDER', default='Cafetería Irazú')   # Nombre del titular
# Google Pay en entorno de prueba: abre la ventana real pero nunca cobra
GOOGLE_PAY_ENVIRONMENT = 'TEST'

# CORREO: Gmail (contraseña de aplicación) > SendGrid > consola
GMAIL_APP_PASSWORD = config('GMAIL_APP_PASSWORD', default='')
SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')
# Si el servidor de correo no responde, se corta a los 10 s en vez de colgar
# la petición (en Render eso provocaba "worker timeout").
EMAIL_TIMEOUT = 10

if GMAIL_APP_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='cuaderno.melanygr@gmail.com')
    EMAIL_HOST_PASSWORD = GMAIL_APP_PASSWORD
    DEFAULT_FROM_EMAIL = f'Cafetería Irazú <{EMAIL_HOST_USER}>'
    CAFE_EMAIL = EMAIL_HOST_USER
elif SENDGRID_API_KEY:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    DEFAULT_FROM_EMAIL = 'cuaderno.melanygr@gmail.com'
    CAFE_EMAIL = 'cuaderno.melanygr@gmail.com'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'cafeteria@localhost.com'
    CAFE_EMAIL = 'cuaderno.melanygr@gmail.com'
