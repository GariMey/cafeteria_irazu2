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