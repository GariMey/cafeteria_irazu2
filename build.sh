#!/usr/bin/env bash
# Comando de construcción para Render: bash build.sh
set -o errexit

pip install -r requirements.txt

# Archivos estáticos (CSS, JS, imágenes de static/) servidos por WhiteNoise
python manage.py collectstatic --no-input

# Tablas de la base de datos (crea también las tarjetas de La Experiencia)
python manage.py migrate --no-input

# Menú inicial: solo la primera vez, cuando la base está vacía
python manage.py load_initial_menu

# Usuario administrador: solo si se definieron las variables en Render
# (DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_PASSWORD y DJANGO_SUPERUSER_EMAIL).
# Si ya existe, no se hace nada.
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
    python manage.py createsuperuser --no-input 2>/dev/null \
        && echo "Usuario administrador creado." \
        || echo "El usuario administrador ya existe."
fi
