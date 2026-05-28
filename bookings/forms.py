from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['customer_name', 'customer_email', 'customer_phone', 'date', 'time', 'guests', 'special_requests']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'contact-input'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'contact-input'}),
            'customer_name': forms.TextInput(attrs={'class': 'contact-input', 'placeholder': 'Tu nombre'}),
            'customer_email': forms.EmailInput(attrs={'class': 'contact-input', 'placeholder': 'tu@email.com'}),
            'customer_phone': forms.TextInput(attrs={'class': 'contact-input', 'placeholder': 'Teléfono'}),
            'guests': forms.NumberInput(attrs={'class': 'contact-input', 'min': 1, 'max': 20}),
            'special_requests': forms.Textarea(attrs={'class': 'contact-input', 'rows': 3, 'placeholder': '¿Alguna solicitud especial?'}),
        }