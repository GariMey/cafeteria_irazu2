import os
from pathlib import Path
from decouple import config 

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-cafeteria-irazu-cartago-costa-rica-2024'
DEBUG = True
ALLOWED_HOSTS = ['*']

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
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', 'postgresql://postgres:GRivera1276@localhost:5432/cafeteria_db')
    )
}

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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CAFE_EMAIL = 'melanygaritauu1276@gmail.com'  # ← Cambia al email donde quieres recibir
# Email configuration (opcional)
#EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Para pruebas
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Para producción
# Configuración para PRODUCCIÓN con Gmail
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'melanygaritauu1276@gmail.com'  # Tu email de Gmail
EMAIL_HOST_PASSWORD = 'ntmnvxkvwwhhgaap'  # La contraseña de 16 dígitos
DEFAULT_FROM_EMAIL = 'Cafetería Irazú <melanygaritauu1276@gmail.com>'
# Se agrego esto para solucionar el error 403 de Django en el deploy
CSRF_TRUSTED_ORIGINS = [
    'https://cafeteria-irazu2.onrender.com',
]
