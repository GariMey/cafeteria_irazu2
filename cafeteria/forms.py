from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Tu nombre',
                'class': 'contact-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'tu@correo.com',
                'class': 'contact-input'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Teléfono (opcional)',
                'class': 'contact-input'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': '¿En qué podemos ayudarte?',
                'rows': 5,
                'class': 'contact-input'
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Correo electrónico',
            'phone': 'Teléfono',
            'message': 'Mensaje',
        }

from django import forms
from .models import Testimonial

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ['name', 'email', 'rating', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'contact-input',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'contact-input',
                'placeholder': 'tu@email.com'
            }),
            'rating': forms.Select(attrs={
                'class': 'contact-input'
            }, choices=[
                (5, '⭐⭐⭐⭐⭐ - Excelente'),
                (4, '⭐⭐⭐⭐ - Muy bueno'),
                (3, '⭐⭐⭐ - Bueno'),
                (2, '⭐⭐ - Regular'),
                (1, '⭐ - Malo'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'contact-input',
                'rows': 4,
                'placeholder': 'Cuéntanos tu experiencia en Cafetería Irazú...'
            }),
        }
        labels = {
            'name': 'Nombre',
            'email': 'Correo electrónico',
            'rating': 'Calificación',
            'comment': 'Tu opinión',
        }