from unittest import mock

from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.test import SimpleTestCase, override_settings

BREVO = override_settings(
    EMAIL_BACKEND='cafeteria_irazu.email_backends.BrevoEmailBackend',
    BREVO_API_KEY='clave-de-prueba',
    DEFAULT_FROM_EMAIL='Cafetería Irazú <cafe@example.com>',
)


def ok_response():
    return mock.Mock(status_code=201, text='{"messageId":"x"}')


@BREVO
class BrevoBackendTests(SimpleTestCase):
    """La API se simula: estas pruebas nunca envían correos reales."""

    @mock.patch('cafeteria_irazu.email_backends.requests.post', return_value=ok_response())
    def test_sends_html_email_with_reply_to(self, post):
        message = EmailMultiAlternatives(
            'Factura FAC-1', 'Texto plano', None, ['María <maria@example.com>'],
            reply_to=['cafe@example.com'],
        )
        message.attach_alternative('<h1>Factura</h1>', 'text/html')
        self.assertEqual(message.send(), 1)

        url = post.call_args.args[0]
        payload = post.call_args.kwargs['json']
        headers = post.call_args.kwargs['headers']
        self.assertEqual(url, 'https://api.brevo.com/v3/smtp/email')
        self.assertEqual(headers['api-key'], 'clave-de-prueba')
        self.assertEqual(payload['sender'], {'email': 'cafe@example.com', 'name': 'Cafetería Irazú'})
        self.assertEqual(payload['to'], [{'email': 'maria@example.com', 'name': 'María'}])
        self.assertEqual(payload['replyTo'], {'email': 'cafe@example.com'})
        self.assertEqual(payload['htmlContent'], '<h1>Factura</h1>')
        self.assertEqual(payload['textContent'], 'Texto plano')
        self.assertEqual(post.call_args.kwargs['timeout'], 10)

    @mock.patch('cafeteria_irazu.email_backends.requests.post',
                return_value=mock.Mock(status_code=401, text='{"message":"Key not found"}'))
    def test_api_error_is_raised(self, post):
        with self.assertRaisesMessage(RuntimeError, 'Brevo respondió 401'):
            EmailMessage('Hola', 'x', None, ['a@example.com']).send()

    @mock.patch('cafeteria_irazu.email_backends.requests.post',
                return_value=mock.Mock(status_code=400, text='error'))
    def test_fail_silently(self, post):
        self.assertEqual(EmailMessage('Hola', 'x', None, ['a@example.com']).send(fail_silently=True), 0)


@override_settings(EMAIL_BACKEND='cafeteria_irazu.email_backends.BrevoEmailBackend',
                   BREVO_API_KEY='xsmtpsib-clave-smtp', DEFAULT_FROM_EMAIL='cafe@example.com')
class BrevoWrongKeyTests(SimpleTestCase):
    @mock.patch('cafeteria_irazu.email_backends.requests.post')
    def test_smtp_key_gives_clear_error(self, post):
        with self.assertRaisesMessage(RuntimeError, 'clave SMTP'):
            EmailMessage('Hola', 'x', None, ['a@example.com']).send()
        post.assert_not_called()


# ── Correos con diseño ─────────────────────────────────────────────────────
from django.core import mail
from django.test import TestCase
from django.urls import reverse


@override_settings(CAFE_EMAIL='cafe@example.com', CAFE_PHONE='6353-1551', CAFE_WHATSAPP='50663531551',
                   EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class BrandedEmailTests(TestCase):
    def test_contact_form_sends_branded_emails(self):
        self.client.post(reverse('home'), {
            'submit_contact': '1', 'name': 'Ana', 'email': 'ana@example.com',
            'phone': '', 'message': '¿Abren los domingos?',
        })
        self.assertEqual(len(mail.outbox), 2)
        to_cafe = next(m for m in mail.outbox if m.to == ['cafe@example.com'])
        to_customer = next(m for m in mail.outbox if m.to == ['ana@example.com'])

        # Responder al aviso de la cafetería le escribe directamente al cliente
        self.assertEqual(to_cafe.reply_to, ['ana@example.com'])
        self.assertIn('/panel/mensajes/', to_cafe.alternatives[0][0])

        html, mimetype = to_customer.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        for expected in ['#1a0f00', '#c4956a', '6353-1551', 'https://wa.me/50663531551', 'mailto:cafe@example.com']:
            self.assertIn(expected, html)
        self.assertIn('¿Abren los domingos?', to_customer.body)
        self.assertIn('6353-1551', to_customer.body)

    def test_reservation_emails_include_cancel_contacts(self):
        from datetime import date, time, timedelta
        from bookings.models import Reservation
        from bookings.notifications import send_confirmed
        reservation = Reservation.objects.create(
            customer_name='Ana', customer_email='ana@example.com', customer_phone='8888-8888',
            date=date.today() + timedelta(days=2), time=time(18, 30), guests=3)
        self.assertTrue(send_confirmed(reservation))
        html = mail.outbox[0].alternatives[0][0]
        self.assertIn('¿No puedes venir?', html)
        self.assertIn('wa.me/50663531551?text=', html)
        self.assertNotIn('..', mail.outbox[0].body.replace('...', ''))
