from django.db import models
from django.utils.text import slugify


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


class Testimonial(models.Model):
    RATING_CHOICES = [(i, '⭐' * i) for i in range(1, 6)]
    name = models.CharField(max_length=100, verbose_name="Nombre")
    comment = models.TextField(verbose_name="Comentario")
    rating = models.IntegerField(choices=RATING_CHOICES, default=5, verbose_name="Calificación")
    active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.rating}⭐"


class ContactMessage(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Correo")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    message = models.TextField(verbose_name="Mensaje")
    read = models.BooleanField(default=False, verbose_name="Leído")
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