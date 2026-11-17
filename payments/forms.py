import json
import re

from django import forms

from .card_validator import CardValidator
from .pricing import DELIVERY, FULFILLMENT_CHOICES, PICKUP

# Letras (incluye tildes y ñ), espacios, apóstrofo, punto y guion
NAME_RE = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ' .\-]+$")
# Teléfonos de Costa Rica: 8 dígitos; fijos empiezan con 2 o 4, móviles con 5-8
CR_PHONE_RE = re.compile(r'^[245678]\d{7}$')
# Comprobante SINPE Móvil: solo dígitos, entre 6 y 30
SINPE_REF_RE = re.compile(r'^\d{6,30}$')

INPUT_CLASS = 'payment-input'

CARD = 'card'
SINPE = 'sinpe'
GOOGLE_PAY = 'google_pay'
APPLE_PAY = 'apple_pay'
WALLETS = (GOOGLE_PAY, APPLE_PAY)
PAYMENT_METHOD_CHOICES = [
    (CARD, 'Tarjeta'),
    (SINPE, 'SINPE Móvil'),
    (GOOGLE_PAY, 'Google Pay'),
    (APPLE_PAY, 'Apple Pay'),
]


def _text(placeholder, **attrs):
    return forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': placeholder, **attrs})


class CheckoutForm(forms.Form):
    """Datos del pedido y del pago.

    Nada de lo que se ingresa aquí se guarda en la base de datos, salvo el
    número de comprobante SINPE (dato de la transacción, no personal) que la
    cafetería necesita para verificar el pago.
    """
    fulfillment = forms.ChoiceField(
        label="¿Cómo quieres recibir tu pedido?",
        choices=FULFILLMENT_CHOICES, initial=PICKUP, widget=forms.RadioSelect,
    )

    customer_name = forms.CharField(
        label="Nombre completo", min_length=3, max_length=100,
        widget=_text('Tu nombre completo', autocomplete='name'),
    )
    customer_email = forms.EmailField(
        label="Correo electrónico", max_length=254,
        widget=forms.EmailInput(attrs={'class': INPUT_CLASS, 'placeholder': 'tu@email.com',
                                       'autocomplete': 'email'}),
    )
    customer_phone = forms.CharField(
        label="Teléfono", max_length=20,
        widget=_text('8888-8888', autocomplete='tel', inputmode='tel'),
    )

    delivery_address = forms.CharField(
        label="Dirección de entrega", required=False, max_length=300,
        widget=forms.Textarea(attrs={'class': INPUT_CLASS, 'rows': 3,
                                     'placeholder': 'Provincia, cantón, distrito y señas exactas',
                                     'autocomplete': 'street-address'}),
    )
    delivery_notes = forms.CharField(
        label="Indicaciones para el repartidor (opcional)", required=False, max_length=200,
        widget=_text('Ej.: portón negro, casa esquinera'),
    )

    # Debe declararse antes que los campos de cada método: sus validaciones
    # consultan qué método se eligió.
    payment_method = forms.ChoiceField(
        label="Método de pago", choices=PAYMENT_METHOD_CHOICES, initial=CARD,
        widget=forms.RadioSelect,
    )

    # ── Tarjeta ──
    card_number = forms.CharField(
        label="Número de tarjeta", max_length=23, required=False,
        widget=_text('1234 5678 9012 3456', autocomplete='cc-number', inputmode='numeric'),
    )
    card_name = forms.CharField(
        label="Nombre en la tarjeta", max_length=100, required=False,
        widget=_text('Como aparece en la tarjeta', autocomplete='cc-name'),
    )
    expiry_date = forms.CharField(
        label="Vencimiento", max_length=7, required=False,
        widget=_text('MM/AA', autocomplete='cc-exp', inputmode='numeric'),
    )
    cvv = forms.CharField(
        label="CVV", max_length=4, required=False,
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASS, 'placeholder': '123',
                                          'autocomplete': 'cc-csc', 'inputmode': 'numeric'}),
    )

    # ── SINPE Móvil ──
    sinpe_reference = forms.CharField(
        label="Número de comprobante SINPE", max_length=40, required=False,
        widget=_text('Ej.: 2026111712345678', inputmode='numeric', autocomplete='off'),
    )

    # ── Billeteras (Google Pay / Apple Pay) ── los llena el JavaScript
    wallet_token = forms.CharField(required=False, max_length=10000, widget=forms.HiddenInput)
    wallet_description = forms.CharField(required=False, max_length=60, widget=forms.HiddenInput)

    CARD_FIELDS = ('card_number', 'card_name', 'expiry_date', 'cvv')
    SECRET_FIELDS = CARD_FIELDS + ('wallet_token', 'wallet_description')

    def _method(self):
        return self.cleaned_data.get('payment_method')

    # ── Contacto ───────────────────────────────────────────────────────────
    def clean_customer_name(self):
        name = ' '.join(self.cleaned_data['customer_name'].split())
        if not NAME_RE.match(name):
            raise forms.ValidationError("El nombre solo puede contener letras y espacios.")
        return name

    def clean_customer_phone(self):
        digits = re.sub(r'[\s\-().]', '', self.cleaned_data['customer_phone'])
        if digits.startswith('+506'):
            digits = digits[4:]
        elif digits.startswith('506') and len(digits) == 11:
            digits = digits[3:]
        if not CR_PHONE_RE.match(digits):
            raise forms.ValidationError("Ingresa un teléfono de Costa Rica válido de 8 dígitos (ej.: 8888-8888).")
        return f"{digits[:4]}-{digits[4:]}"

    def clean_delivery_address(self):
        return ' '.join(self.cleaned_data['delivery_address'].split())

    # ── Tarjeta (solo si se paga con tarjeta) ──────────────────────────────
    def clean_card_number(self):
        if self._method() != CARD:
            return ''
        value = self.cleaned_data['card_number']
        if not value:
            raise forms.ValidationError("Ingresa el número de tarjeta.")
        ok, msg, brand = CardValidator.validate_card_number(value)
        if not ok:
            raise forms.ValidationError(msg)
        self._card_brand = brand
        return re.sub(r'[\s\-]', '', value)

    def clean_card_name(self):
        if self._method() != CARD:
            return ''
        name = ' '.join(self.cleaned_data['card_name'].split())
        if len(name) < 3:
            raise forms.ValidationError("Ingresa el nombre del titular como aparece en la tarjeta.")
        if not NAME_RE.match(name):
            raise forms.ValidationError("El nombre del titular solo puede contener letras y espacios.")
        return name.upper()

    def clean_expiry_date(self):
        if self._method() != CARD:
            return ''
        value = self.cleaned_data['expiry_date']
        if not value:
            raise forms.ValidationError("Ingresa la fecha de vencimiento.")
        ok, msg, _month, _year = CardValidator.validate_expiry_date(value)
        if not ok:
            raise forms.ValidationError(msg)
        return value

    def clean_cvv(self):
        if self._method() != CARD:
            return ''
        value = self.cleaned_data['cvv']
        if not value:
            raise forms.ValidationError("Ingresa el CVV.")
        # Si el número es inválido no se conoce la marca; se valida como 3 o 4 dígitos
        brand = getattr(self, '_card_brand', None)
        ok, msg = CardValidator.validate_cvv(value, brand)
        if not ok and brand is None and re.fullmatch(r'\d{3,4}', value):
            ok = True
        if not ok:
            raise forms.ValidationError(msg)
        return value

    # ── SINPE Móvil ────────────────────────────────────────────────────────
    def clean_sinpe_reference(self):
        if self._method() != SINPE:
            return ''
        ref = re.sub(r'[\s\-]', '', self.cleaned_data['sinpe_reference'])
        if not ref:
            raise forms.ValidationError("Ingresa el número de comprobante que te dio tu banco.")
        if not SINPE_REF_RE.match(ref):
            raise forms.ValidationError("El comprobante debe tener solo números (entre 6 y 30 dígitos).")
        return ref

    # ── Billeteras ─────────────────────────────────────────────────────────
    def clean_wallet_token(self):
        method = self._method()
        if method not in WALLETS:
            return ''
        token = self.cleaned_data['wallet_token'].strip()
        if not token:
            raise forms.ValidationError("Completa el pago en la ventana de la billetera.")
        if method == GOOGLE_PAY and token.startswith('{'):
            # Token real de Google Pay (entorno de prueba): debe ser JSON válido
            try:
                json.loads(token)
            except ValueError:
                raise forms.ValidationError("La respuesta de Google Pay no es válida. Intenta de nuevo.")
        return token

    def clean_wallet_description(self):
        if self._method() not in WALLETS:
            return ''
        return ' '.join(self.cleaned_data['wallet_description'].split())

    # ── Validaciones que dependen de varios campos ─────────────────────────
    def clean(self):
        cleaned = super().clean()

        if cleaned.get('fulfillment') == DELIVERY:
            address = cleaned.get('delivery_address', '')
            if not address:
                self.add_error('delivery_address', "Indica la dirección para la entrega a domicilio.")
            elif len(address) < 15:
                self.add_error('delivery_address', "Agrega más detalles: provincia, cantón y señas.")
        else:
            # Si recoge en tienda, no se necesita (ni se usa) la dirección
            cleaned['delivery_address'] = ''
            cleaned['delivery_notes'] = ''

        # El token de billetera debe venir junto al método que lo generó
        if self.errors.get('wallet_token') and cleaned.get('payment_method') in WALLETS:
            self.add_error(None, "No se completó el pago con la billetera.")

        return cleaned

    @property
    def payment_summary(self):
        """Descripción del pago para los correos (sin datos sensibles)."""
        method = self.cleaned_data.get('payment_method')
        if method == CARD:
            brand = getattr(self, '_card_brand', None)
            name = CardValidator.BRAND_NAMES.get(brand, brand or 'Tarjeta')
            return f"Tarjeta {name} terminada en {self.cleaned_data['card_number'][-4:]}"
        if method == SINPE:
            return f"SINPE Móvil - comprobante {self.cleaned_data['sinpe_reference']} (pendiente de verificación)"
        label = dict(PAYMENT_METHOD_CHOICES)[method]
        detail = self.cleaned_data.get('wallet_description')
        return f"{label} - {detail}" if detail else label

    def clear_secret_data(self):
        """Evita que los datos de pago se vuelvan a mostrar al re-renderizar."""
        if self.is_bound:
            data = self.data.copy()
            for field in self.SECRET_FIELDS:
                data[field] = ''
            self.data = data
