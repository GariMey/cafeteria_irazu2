import os
from pathlib import Path
from decouple import config
import sendgrid

BASE_DIR = Path(__file__).resolve().parent.parent

# VARIABLES DE ENTORNO

SECRET_KEY = config('SECRET_KEY', default='django-insecure-cafeteria-irazu-cartago-costa-rica-2024')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

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

# BASE DE DATOS
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
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

# ALMACENAMIENTO DE ARCHIVOS
# Si existe CLOUDINARY_URL, las imágenes subidas (productos, galería) se guardan
# en Cloudinary; si no, se guardan en la carpeta media/ local.
CLOUDINARY_URL = config('CLOUDINARY_URL', default='')

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}

if CLOUDINARY_URL:
    # La librería de Cloudinary lee la variable desde el entorno del sistema
    os.environ.setdefault('CLOUDINARY_URL', CLOUDINARY_URL)
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


# EMAIL CONFIGURATION CON SENDGRID

SENDGRID_API_KEY = config('SENDGRID_API_KEY', default='')

def send_sendgrid_email(subject, html_content, to_emails, from_email='cuaderno.melanygr@gmail.com'):
    """Función para enviar correos con SendGrid"""
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = sendgrid.From(from_email)
        to_email = sendgrid.To(to_emails[0])
        content = sendgrid.Content("text/plain", html_content)
        mail = sendgrid.Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        return response.status_code == 202
    except Exception as e:
        print(f"Error SendGrid: {e}")
        return False

GMAIL_APP_PASSWORD = config('GMAIL_APP_PASSWORD', default='')

if GMAIL_APP_PASSWORD:
    # Envío directo por Gmail con contraseña de aplicación
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='cuaderno.melanygr@gmail.com')
    EMAIL_HOST_PASSWORD = GMAIL_APP_PASSWORD
    DEFAULT_FROM_EMAIL = f'Cafetería Irazú <{EMAIL_HOST_USER}>'
    CAFE_EMAIL = EMAIL_HOST_USER
elif SENDGRID_API_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey'
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    DEFAULT_FROM_EMAIL = 'cuaderno.melanygr@gmail.com'
    CAFE_EMAIL = 'cuaderno.melanygr@gmail.com'
else:
    # Fallback a consola
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'cafeteria@localhost.com'
    CAFE_EMAIL = 'cuaderno.melanygr@gmail.com'
    
CSRF_TRUSTED_ORIGINS = [
    'https://cafeteria-irazu2-4tub.onrender.com',
]