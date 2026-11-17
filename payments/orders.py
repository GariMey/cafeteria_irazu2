"""Cambios de estado de los pedidos desde el panel del negocio.

Al cerrar un pedido (Entregado o Cancelado) se borran los datos de contacto
del cliente. Como respaldo, purge_stale_contacts() los borra de pedidos que
quedaron abiertos más de ORDER_CONTACT_RETENTION_DAYS días.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .invoices import reject_sinpe
from .models import Payment


class OrderError(Exception):
    """Cambio de estado no permitido (el mensaje se muestra en el panel)."""


def advance_order(payment, new_status):
    """Avanza el pedido al siguiente estado del flujo."""
    if new_status not in payment.next_order_statuses():
        if payment.awaiting_sinpe:
            raise OrderError("Primero confirma el pago SINPE.")
        raise OrderError("Ese cambio de estado no es válido para este pedido.")
    payment.order_status = new_status
    if new_status == Payment.DELIVERED:
        payment.forget_contact()
    payment.save()


def cancel_order(payment):
    """Cancela un pedido activo y borra los datos del cliente.

    Un SINPE sin verificar se rechaza (avisa al cliente); un pago ya
    completado queda como reembolsado (simulado: no hay cobro real).
    """
    if not payment.is_active_order:
        raise OrderError("El pedido ya está cerrado.")
    if payment.awaiting_sinpe:
        reject_sinpe(payment)
        return
    if payment.status == 'completed':
        payment.status = 'refunded'
    payment.order_status = Payment.CANCELLED
    payment.forget_contact()
    payment.save()


def purge_stale_contacts():
    """Borra el contacto de pedidos abiertos demasiado tiempo. Devuelve cuántos."""
    days = int(getattr(settings, 'ORDER_CONTACT_RETENTION_DAYS', 7))
    limit = timezone.now() - timedelta(days=days)
    return (Payment.objects.filter(created_at__lt=limit)
            .exclude(contact_name='', contact_email='', contact_phone='', delivery_address='')
            .update(**{field: '' for field in Payment.CONTACT_FIELDS}))
