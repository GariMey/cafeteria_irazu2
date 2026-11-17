"""Cálculo de totales del pedido: subtotal, IVA y costo de envío.

Todo el dinero se calcula en el servidor con Decimal; el navegador solo
muestra una vista previa y nunca decide cuánto se cobra.
"""
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings

PICKUP = 'pickup'
DELIVERY = 'delivery'
FULFILLMENT_CHOICES = [
    (PICKUP, 'Recoger en tienda'),
    (DELIVERY, 'Entrega a domicilio'),
]

TWO_PLACES = Decimal('0.01')


def iva_rate():
    """Tasa de IVA (13 % en Costa Rica). Configurable con settings.IVA_RATE."""
    return Decimal(str(getattr(settings, 'IVA_RATE', '0.13')))


def delivery_fee():
    """Costo fijo de envío a domicilio. Configurable con settings.DELIVERY_FEE."""
    return Decimal(str(getattr(settings, 'DELIVERY_FEE', '1500')))


def _money(value):
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_totals(subtotal, fulfillment=PICKUP):
    """Devuelve subtotal, IVA, envío y total para el tipo de entrega dado.

    El IVA se aplica a los productos y también al envío, porque en Costa Rica
    el servicio de entrega está gravado.
    """
    subtotal = _money(Decimal(subtotal))
    shipping = delivery_fee() if fulfillment == DELIVERY else Decimal('0')
    tax = _money((subtotal + shipping) * iva_rate())
    return {
        'subtotal': subtotal,
        'tax': tax,
        'tax_percent': int(iva_rate() * 100),
        'delivery_fee': _money(shipping),
        'total': _money(subtotal + shipping + tax),
    }
