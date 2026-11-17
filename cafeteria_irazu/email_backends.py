"""Envío de correos por la API HTTPS de Brevo.

Render (plan gratuito) bloquea las conexiones SMTP salientes, así que Gmail
por SMTP no funciona allí. La API de Brevo usa HTTPS (puerto 443), que sí
está permitido. Se activa con la variable BREVO_API_KEY (ver settings.py).
"""
import logging
from email.utils import getaddresses, parseaddr

import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

BREVO_URL = 'https://api.brevo.com/v3/smtp/email'


def _contact(address):
    name, email = parseaddr(address)
    contact = {'email': email}
    if name:
        contact['name'] = name
    return contact


def _contacts(addresses):
    return [_contact(f'{name} <{email}>' if name else email)
            for name, email in getaddresses(addresses) if email]


class BrevoEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', None) or 10

    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages:
            try:
                self._send(message)
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
                logger.exception("Brevo no pudo enviar el correo «%s»", message.subject)
        return sent

    def _send(self, message):
        if self.api_key.startswith('xsmtpsib-'):
            # Error frecuente: en Brevo la clave SMTP y la de API están en la misma página
            raise RuntimeError("BREVO_API_KEY es una clave SMTP (xsmtpsib-…). Usa una clave de API "
                               "(xkeysib-…) de Brevo: SMTP & API → pestaña API Keys.")
        payload = {
            'sender': _contact(message.from_email or settings.DEFAULT_FROM_EMAIL),
            'to': _contacts(message.to),
            'subject': message.subject,
            'textContent': message.body or ' ',
        }
        if message.cc:
            payload['cc'] = _contacts(message.cc)
        if message.bcc:
            payload['bcc'] = _contacts(message.bcc)
        if message.reply_to:
            payload['replyTo'] = _contact(message.reply_to[0])
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                payload['htmlContent'] = content

        response = requests.post(
            BREVO_URL, json=payload, timeout=self.timeout,
            headers={'api-key': self.api_key, 'accept': 'application/json'},
        )
        if response.status_code >= 400:
            # El cuerpo de la respuesta de Brevo explica el problema (no incluye la clave)
            raise RuntimeError(f"Brevo respondió {response.status_code}: {response.text[:300]}")
