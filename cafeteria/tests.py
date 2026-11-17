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
