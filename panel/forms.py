from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from cafeteria.models import ExperienceFeature, GalleryImage, Product

MAX_IMAGE_MB = 5
MAX_GALLERY_FILES = 12


def _check_size(image):
    if image and getattr(image, 'size', 0) > MAX_IMAGE_MB * 1024 * 1024:
        raise forms.ValidationError(f"La imagen «{image.name}» pesa más de {MAX_IMAGE_MB} MB.")
    return image


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    """Acepta varias imágenes en un solo campo (cada una se valida con Pillow)."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleImageInput(attrs={'accept': 'image/*', 'class': 'block w-full text-sm'}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        files = data if isinstance(data, (list, tuple)) else [data]
        files = [f for f in files if f]
        if not files:
            raise forms.ValidationError("Elige al menos una imagen.")
        if len(files) > MAX_GALLERY_FILES:
            raise forms.ValidationError(f"Puedes subir hasta {MAX_GALLERY_FILES} fotos a la vez.")
        return [_check_size(super(MultipleImageField, self).clean(f, initial)) for f in files]


class GalleryUploadForm(forms.Form):
    images = MultipleImageField(label="Fotos")


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full rounded-lg border border-latte/40 px-2 py-1 text-sm',
                                            'placeholder': 'Título (opcional)'}),
            'order': forms.NumberInput(attrs={'class': 'w-20 rounded-lg border border-latte/40 px-2 py-1 text-sm', 'min': 0}),
        }


class StaffLoginForm(AuthenticationForm):
    """Login del panel: solo deja entrar al personal (is_staff)."""

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError("Esta cuenta no tiene acceso al panel.", code='no_staff')

INPUT = ('w-full rounded-lg border border-latte/40 bg-white px-3 py-2 text-espresso '
         'focus:outline-none focus:ring-2 focus:ring-latte')


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description', 'price', 'image', 'available', 'featured']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT}),
            'category': forms.Select(attrs={'class': INPUT}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': INPUT, 'min': '1', 'step': '50'}),
            'image': forms.ClearableFileInput(attrs={'class': 'block w-full text-sm', 'accept': 'image/*'}),
        }
        help_texts = {
            'image': 'Opcional. Si no subes una, se usa la de static/img/ con el mismo nombre del producto.',
            'available': 'Desmárcalo si el producto está agotado: deja de aparecer en el menú.',
            'featured': 'Aparece en la sección de destacados de la página de inicio.',
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price is None or price <= 0:
            raise forms.ValidationError("El precio debe ser mayor que cero.")
        if price > Decimal('1000000'):
            raise forms.ValidationError("Revisa el precio: parece demasiado alto.")
        return price

    def clean_name(self):
        return ' '.join(self.cleaned_data['name'].split())


class ExperienceFeatureForm(forms.ModelForm):
    class Meta:
        model = ExperienceFeature
        fields = ['icon', 'title', 'description', 'image', 'order', 'active']
        widgets = {
            'icon': forms.TextInput(attrs={'class': INPUT, 'placeholder': '🏔️', 'maxlength': 10}),
            'title': forms.TextInput(attrs={'class': INPUT}),
            'description': forms.Textarea(attrs={'class': INPUT, 'rows': 3, 'maxlength': 300}),
            'image': forms.ClearableFileInput(attrs={'class': 'block w-full text-sm', 'accept': 'image/*'}),
            'order': forms.NumberInput(attrs={'class': INPUT, 'min': 0}),
        }
        help_texts = {
            'icon': 'Un emoji que aparece junto al título.',
            'image': 'Mejor horizontal (16:10), máximo 5 MB. Si no subes una, se mantiene la imagen actual.',
            'order': 'Las tarjetas se muestran de menor a mayor.',
            'active': 'Desmárcalo para ocultar la tarjeta sin borrarla.',
        }

    def clean_image(self):
        return _check_size(self.cleaned_data.get('image'))

    def clean_title(self):
        return ' '.join(self.cleaned_data['title'].split())


class ReplyForm(forms.Form):
    subject = forms.CharField(
        label="Asunto", max_length=150,
        widget=forms.TextInput(attrs={'class': INPUT}),
    )
    body = forms.CharField(
        label="Respuesta", min_length=5, max_length=5000,
        widget=forms.Textarea(attrs={'class': INPUT, 'rows': 7,
                                     'placeholder': 'Escribe tu respuesta al cliente…'}),
    )
