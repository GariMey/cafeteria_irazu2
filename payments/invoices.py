"""Facturas y avisos al cliente cuando cambia el estado de un pago.

- Tarjeta / Google Pay / Apple Pay: la factura se envía al momento del pago.
- SINPE Móvil: la factura se envía cuando la cafetería confirma el depósito
  en el admin; si lo rechaza, se avisa al cliente.

En ambos casos el nombre y correo temporales del pedido se borran después.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .pricing import DELIVERY, iva_rate

logger = logging.getLogger(__name__)


def payment_detail(payment):
    """Descripción del medio de pago que se puede reconstruir desde la base."""
    if payment.payment_method == 'sinpe':
        return f"SINPE Móvil - comprobante {payment.reference}"
    return payment.get_payment_method_display()


def _send(subject, template, context, to_email):
    text = render_to_string(f'emails/{template}.txt', context)
    html = render_to_string(f'emails/{template}.html', context)
    message = EmailMultiAlternatives(subject, text, settings.DEFAULT_FROM_EMAIL, [to_email])
    message.attach_alternative(html, 'text/html')
    message.send()


def _forget_contact(payment):
    payment.pending_customer_name = ''
    payment.pending_customer_email = ''


def send_invoice(payment, customer_name, customer_email, detail=None):
    """Envía la factura del pago confirmado. Devuelve True si se envió.

    No hace nada si el pago no está completado o si la factura ya se envió.
    """
    if payment.status != 'completed' or payment.invoiced_at or not customer_email:
        return False

    issued_at = timezone.now()
    invoice_number = f"FAC-{payment.id:08d}"
    context = {
        'payment': payment,
        'items': payment.items.all(),
        'invoice_number': invoice_number,
        'issued_at': timezone.localtime(issued_at),
        'customer_name': customer_name,
        'customer_email': customer_email,
        'payment_detail': detail or payment_detail(payment),
        'is_delivery': payment.fulfillment == DELIVERY,
        'tax_percent': int(iva_rate() * 100),
        'business': {
            'name': 'Cafetería Irazú',
            'address': 'Camino al Volcán Irazú, Cartago, Costa Rica',
            'phone': '6353-1551',
            'email': settings.CAFE_EMAIL,
        },
    }
    try:
        _send(f'Factura {invoice_number} - Cafetería Irazú', 'invoice', context, customer_email)
    except Exception:
        # No se registra el correo del cliente en los logs
        logger.exception("No se pudo enviar la factura del pedido %s", payment.transaction_id)
        return False

    payment.invoice_number = invoice_number
    payment.invoiced_at = issued_at
    _forget_contact(payment)
    payment.save(update_fields=['invoice_number', 'invoiced_at',
                                'pending_customer_name', 'pending_customer_email'])
    return True


def confirm_sinpe(payment):
    """Marca un SINPE como pagado y envía la factura con el contacto guardado.

    Devuelve True si la factura se envió.
    """
    if payment.status != 'completed':
        payment.status = 'completed'
        payment.save(update_fields=['status'])
    return send_invoice(payment, payment.pending_customer_name, payment.pending_customer_email)


def reject_sinpe(payment):
    """Marca un SINPE como fallido, avisa al cliente y borra su contacto."""
    email = payment.pending_customer_email
    if payment.status != 'failed':
        payment.status = 'failed'
    if email:
        context = {
            'payment': payment,
            'customer_name': payment.pending_customer_name,
            'cafe_phone': '6353-1551',
            'cafe_email': settings.CAFE_EMAIL,
        }
        try:
            _send(f'No pudimos verificar tu pago - {payment.transaction_id}',
                  'sinpe_rejected', context, email)
        except Exception:
            logger.exception("No se pudo avisar el rechazo del pedido %s", payment.transaction_id)
    _forget_contact(payment)
    payment.save(update_fields=['status', 'pending_customer_name', 'pending_customer_email'])
