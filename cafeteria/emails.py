"""Correos con el diseño de la cafetería.

Cada correo tiene dos versiones: templates/emails/<nombre>.html (con los
colores del sitio) y templates/emails/<nombre>.txt (texto plano para los
programas de correo que no muestran HTML). Ambas extienden base.html/base.txt,
que incluyen el encabezado, los medios de contacto y el pie.
"""
import logging
from urllib.parse import quote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def brand_context(reference=''):
    """Datos del negocio para las plantillas. `reference` (n.º de pedido o
    reserva) se agrega al mensaje de WhatsApp y al asunto del correo."""
    phone_digits = ''.join(ch for ch in settings.CAFE_PHONE if ch.isdigit())
    whatsapp_text = "Hola, Cafetería Irazú. " + (f"Les escribo por {reference}." if reference else "")
    mail_subject = f"Consulta sobre {reference}" if reference else "Consulta"
    return {
        'cafe': {
            'name': 'Cafetería Irazú',
            'tagline': 'Café artesanal camino al volcán Irazú',
            'phone': settings.CAFE_PHONE,
            'phone_link': f'tel:+506{phone_digits}',
            'whatsapp_link': f'https://wa.me/{settings.CAFE_WHATSAPP}?text={quote(whatsapp_text)}',
            'whatsapp_short': f'https://wa.me/{settings.CAFE_WHATSAPP}',
            'email': settings.CAFE_EMAIL,
            'email_link': f'mailto:{settings.CAFE_EMAIL}?subject={quote(mail_subject)}',
            'address': settings.CAFE_ADDRESS,
            'site_url': settings.SITE_URL,
        },
        'reference': reference,
    }


def send_branded(subject, template, context, to, reference='', reply_to=None):
    """Envía un correo con diseño. Lanza la excepción si falla (el llamador decide)."""
    full_context = {**brand_context(reference), **context}
    text = render_to_string(f'emails/{template}.txt', full_context)
    html = render_to_string(f'emails/{template}.html', full_context)
    message = EmailMultiAlternatives(
        subject, text, settings.DEFAULT_FROM_EMAIL, list(to),
        reply_to=reply_to or [settings.CAFE_EMAIL],
    )
    message.attach_alternative(html, 'text/html')
    message.send()


def try_send_branded(*args, **kwargs):
    """Igual que send_branded, pero devuelve True/False y registra el error sin datos personales."""
    try:
        send_branded(*args, **kwargs)
        return True
    except Exception:
        logger.exception("No se pudo enviar el correo «%s»", args[0] if args else kwargs.get('subject'))
        return False
