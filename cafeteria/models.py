import unicodedata

from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.utils.text import slugify

PRODUCT_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.avif'}


def _normalize_image_name(name):
    """'Café_Chorreado' y 'café chorreado' quedan iguales para compararlos."""
    name = unicodedata.normalize('NFC', name).replace('_', ' ')
    return ' '.join(name.split()).casefold()


def _find_static_product_image(product_name):
    """Nombre del archivo en static/img/ que corresponde al producto, o None."""
    folder = settings.BASE_DIR / 'static' / 'img'
    if not folder.is_dir():
        return None
    target = _normalize_image_name(product_name)
    for path in folder.iterdir():
        if path.suffix.lower() in PRODUCT_IMAGE_EXTENSIONS and _normalize_image_name(path.stem) == target:
            return path.name
    return None


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True, verbose_name="Ícono (emoji)")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre")
    description = models.TextField(verbose_name="Descripción")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Precio (₡)")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Imagen")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Categoría")
    featured = models.BooleanField(default=False, verbose_name="Destacado")
    available = models.BooleanField(default=True, verbose_name="Disponible")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['category', 'name']

    @property
    def image_url(self):
        """URL de la imagen del producto.

        Usa la imagen subida desde el admin; si no hay, busca en static/img/
        un archivo con el mismo nombre del producto (sin importar mayúsculas,
        extensión ni si usa '_' en vez de espacios). Devuelve '' si no hay.
        """
        if self.image:
            return self.image.url
        filename = _find_static_product_image(self.name)
        return static(f'img/{filename}') if filename else ''

    def __str__(self):
        return self.name


class GalleryImage(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título", blank=True)
    image = models.ImageField(upload_to='gallery/', verbose_name="Imagen")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        verbose_name = "Imagen de Galería"
        verbose_name_plural = "Galería"
        ordering = ['order']

    def __str__(self):
        return self.title or f"Imagen {self.pk}"


class ExperienceFeature(models.Model):
    """Tarjeta de la sección «La Experiencia Irazú» de la página de inicio."""
    icon = models.CharField(max_length=10, blank=True, verbose_name="Ícono (emoji)")
    title = models.CharField(max_length=80, verbose_name="Título")
    description = models.TextField(max_length=300, verbose_name="Descripción")
    image = models.ImageField(upload_to='experience/', blank=True, null=True, verbose_name="Imagen")
    # Imagen incluida en el proyecto (static/img/...), usada si no se sube otra
    static_image = models.CharField(max_length=200, blank=True, editable=False)
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    active = models.BooleanField(default=True, verbose_name="Visible")

    class Meta:
        verbose_name = "Tarjeta de La Experiencia"
        verbose_name_plural = "La Experiencia Irazú"
        ordering = ['order', 'id']

    def __str__(self):
        return self.title

    @property
    def image_url(self):
        if self.image:
            return self.image.url
        return static(self.static_image) if self.static_image else ''


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Correo")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    message = models.TextField(verbose_name="Mensaje")
    read = models.BooleanField(default=False, verbose_name="Leído")
    # Respuesta enviada desde el panel del negocio (llega al cliente por correo)
    reply = models.TextField(blank=True, verbose_name="Respuesta")
    replied_at = models.DateTimeField(null=True, blank=True, verbose_name="Respondido")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Mensaje de Contacto"
        verbose_name_plural = "Mensajes de Contacto"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.email}"

class Testimonial(models.Model):
    RATING_CHOICES = [(i, '⭐' * i) for i in range(1, 6)]
    name = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Email", blank=True, null=True)
    comment = models.TextField(verbose_name="Comentario")
    rating = models.IntegerField(choices=RATING_CHOICES, default=5, verbose_name="Calificación")
    active = models.BooleanField(default=True, verbose_name="Activo")  # False = requiere aprobación
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating}⭐"