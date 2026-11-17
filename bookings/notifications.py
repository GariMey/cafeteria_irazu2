"""Correos al cliente cuando cambia el estado de su reserva."""
import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import formats

logger = logging.getLogger(__name__)

CAFE_PHONE = '6353-1551'


def _when(reservation):
    fecha = formats.date_format(reservation.date, 'l j \\d\\e F')
    hora = reservation.time.strftime('%I:%M %p').lstrip('0')
    return fecha, hora


def _send(reservation, subject, body):
    """Envía el correo y devuelve True si salió. Nunca registra datos del cliente."""
    message = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [reservation.customer_email],
                           reply_to=[settings.CAFE_EMAIL])
    try:
        message.send()
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo de la reserva %s", reservation.pk)
        return False


def received_body(reservation):
    fecha, hora = _when(reservation)
    return f"""Hola {reservation.customer_name},

¡Gracias por reservar en Cafetería Irazú! Recibimos tu solicitud:

   Fecha: {fecha}
   Hora: {hora}
   Personas: {reservation.guests}

Te enviaremos otro correo en cuanto confirmemos tu mesa.
Si necesitas cambiar algo, llámanos al {CAFE_PHONE}.

Cafetería Irazú - Cartago, Costa Rica
"""


def send_confirmed(reservation):
    fecha, hora = _when(reservation)
    mesa = f"\n   Mesa: {reservation.table.number}" if reservation.table else ""
    return _send(reservation, 'Reserva confirmada - Cafetería Irazú', f"""Hola {reservation.customer_name},

¡Tu reserva está confirmada! Te esperamos:

   Fecha: {fecha}
   Hora: {hora}
   Personas: {reservation.guests}{mesa}

Si no puedes venir, avísanos al {CAFE_PHONE} para liberar la mesa.

Cafetería Irazú - Cartago, Costa Rica
""")


def send_cancelled(reservation):
    fecha, hora = _when(reservation)
    return _send(reservation, 'Reserva cancelada - Cafetería Irazú', f"""Hola {reservation.customer_name},

Lamentamos informarte que tu reserva del {fecha} a las {hora} para {reservation.guests} persona(s)
fue cancelada.

Si quieres buscar otra fecha u hora, llámanos al {CAFE_PHONE} o vuelve a reservar en nuestro sitio.

Cafetería Irazú - Cartago, Costa Rica
""")
