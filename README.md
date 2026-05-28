# ☕ Cafetería Irazú — Sitio Web Oficial

Sitio web profesional para **Cafetería Irazú**, ubicada en Cartago, Costa Rica, camino al volcán Irazú.

---

## 🚀 Instalación rápida

### 1. Requisitos
- Python 3.10+
- pip

### 2. Clonar e instalar
```bash
# Instalar dependencias
pip install django pillow python-dotenv

# Ir al directorio del proyecto
cd cafeteria_irazu

# Ejecutar migraciones
python manage.py makemigrations cafeteria
python manage.py migrate

# Cargar datos de ejemplo (opcional)
python manage.py shell < seed_data.py

# Crear superusuario
python manage.py createsuperuser

# Iniciar servidor
python manage.py runserver
```

### 3. Acceder al sitio
- **Sitio público:** http://localhost:8000/
- **Panel de administración:** http://localhost:8000/admin/
- **Credenciales demo:** admin / irazu2024

---

## 📁 Estructura del proyecto

```
cafeteria_irazu/
├── cafeteria/              # App principal
│   ├── models.py           # Modelos: Category, Product, Gallery, Testimonial, Contact
│   ├── views.py            # Vistas principales
│   ├── admin.py            # Admin personalizado
│   ├── forms.py            # Formulario de contacto
│   └── urls.py             # URLs de la app
├── cafeteria_irazu/        # Configuración del proyecto
│   ├── settings.py
│   └── urls.py
├── templates/              # Templates HTML
│   ├── base.html           # Template base
│   ├── partials/
│   │   ├── navbar.html     # Navegación
│   │   └── footer.html     # Pie de página
│   └── cafeteria/
│       ├── home.html       # Página principal (One-page)
│       └── menu.html       # Menú completo
├── static/
│   ├── css/main.css        # Estilos personalizados
│   └── js/main.js          # JavaScript
├── media/                  # Imágenes subidas
└── db.sqlite3              # Base de datos SQLite
```

---

## 🎨 Tecnologías

| Tecnología | Uso |
|-----------|-----|
| Django 6.x | Backend / ORM / Admin |
| TailwindCSS CDN | Estilos responsive |
| SQLite | Base de datos |
| Pillow | Manejo de imágenes |
| Google Fonts (Cormorant Garamond + Jost) | Tipografía |

---

## 🛠️ Administración

Desde el panel de Django Admin puedes:

- ✅ **Productos** — Agregar/editar/eliminar con imagen, precio, categoría
- ✅ **Categorías** — Organizar el menú con íconos y orden
- ✅ **Galería** — Gestionar fotos del lugar
- ✅ **Testimonios** — Publicar/ocultar reseñas de clientes
- ✅ **Mensajes de contacto** — Ver mensajes recibidos desde el formulario

---

## 📞 Información del negocio

- **Nombre:** Cafetería Irazú
- **Dirección:** V4VF+96F, Ruta 219, Cot, Cartago Province
- **Teléfono:** 6433-2241
- **Calificación:** ⭐ 4.5 (380+ reseñas)

---

## 🚀 Producción

Para desplegar en producción (Heroku, Railway, etc.):

1. Cambiar `DEBUG = False` en settings.py
2. Configurar `ALLOWED_HOSTS`
3. Usar PostgreSQL en lugar de SQLite
4. Configurar variables de entorno con `.env`
5. Ejecutar `python manage.py collectstatic`

