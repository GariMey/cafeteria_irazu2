from django import forms
from .models import Payment

class PaymentForm(forms.ModelForm):
    card_number = forms.CharField(
        label="Número de tarjeta",
        widget=forms.TextInput(attrs={
            'placeholder': '1234 5678 9012 3456',
            'class': 'payment-input',
            'maxlength': '19'
        }),
        required=True
    )
    card_name = forms.CharField(
        label="Nombre en la tarjeta",
        widget=forms.TextInput(attrs={
            'placeholder': 'COMO APARECE EN LA TARJETA',
            'class': 'payment-input'
        }),
        required=True
    )
    expiry_date = forms.CharField(
        label="Fecha de expiración",
        widget=forms.TextInput(attrs={
            'placeholder': 'MM/AA',
            'class': 'payment-input',
            'maxlength': '5'
        }),
        required=True
    )
    cvv = forms.CharField(
        label="CVV",
        widget=forms.TextInput(attrs={
            'placeholder': '123',
            'class': 'payment-input',
            'maxlength': '4'
        }),
        required=True
    )
    
    class Meta:
        model = Payment
        fields = ['customer_name', 'customer_email', 'customer_phone', 'payment_method']
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'payment-input', 'placeholder': 'Tu nombre completo'}),
            'customer_email': forms.EmailInput(attrs={'class': 'payment-input', 'placeholder': 'tu@email.com'}),
            'customer_phone': forms.TextInput(attrs={'class': 'payment-input', 'placeholder': 'Teléfono'}),
            'payment_method': forms.Select(attrs={'class': 'payment-input'}),
        }