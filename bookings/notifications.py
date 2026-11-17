"""Correos de reservas (con el diseño de la cafetería: templates/emails/reservation_*)."""
from django.conf import settings
from django.utils import formats

from cafeteria.emails import try_send_branded


def _context(reservation):
    fecha = formats.date_format(reservation.date, 'l j \\d\\e F').capitalize()
    hora = reservation.time.strftime('%I:%M %p').lstrip('0').replace('AM', 'a. m.').replace('PM', 'p. m.')
    # Referencia neutra: se usa en "indícanos …" y en el mensaje de WhatsApp que escribe el cliente
    return {'reservation': reservation, 'fecha': fecha, 'hora': hora}, f"la reserva del {fecha} ({hora})"


def _send_to_customer(reservation, subject, template):
    context, reference = _context(reservation)
    return try_send_branded(subject, template, context, [reservation.customer_email], reference=reference)


def send_received(reservation):
    return _send_to_customer(reservation, 'Recibimos tu reserva - Cafetería Irazú', 'reservation_received')


def send_confirmed(reservation):
    return _send_to_customer(reservation, 'Reserva confirmada - Cafetería Irazú', 'reservation_confirmed')


def send_cancelled(reservation):
    return _send_to_customer(reservation, 'Reserva cancelada - Cafetería Irazú', 'reservation_cancelled')


def send_new_to_cafe(reservation):
    context, reference = _context(reservation)
    context['rows'] = [('Cliente', reservation.customer_name), ('Teléfono', reservation.customer_phone),
                       ('Correo', reservation.customer_email)]
    return try_send_branded('Nueva reserva - Cafetería Irazú', 'reservation_new_cafe', context,
                            [settings.CAFE_EMAIL], reference=reference,
                            reply_to=[reservation.customer_email])
