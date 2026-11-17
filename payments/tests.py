from datetime import date
from decimal import Decimal

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from cafeteria.models import Category, Product
from cart.models import Cart, CartItem

from .card_validator import CardValidator
from .forms import CheckoutForm
from .models import Payment
from .pricing import calculate_totals

NEXT_YEAR = str(date.today().year + 1)[-2:]


def valid_data(**overrides):
    data = {
        'fulfillment': 'pickup',
        'customer_name': 'María Pérez',
        'customer_email': 'maria@example.com',
        'customer_phone': '8888-8888',
        'delivery_address': '',
        'delivery_notes': '',
        'payment_method': 'card',
        'card_number': '4111 1111 1111 1111',
        'card_name': 'Maria Perez',
        'expiry_date': f'12/{NEXT_YEAR}',
        'cvv': '123',
    }
    data.update(overrides)
    return data


@override_settings(IVA_RATE='0.13', DELIVERY_FEE='1500')
class PricingTests(TestCase):
    def test_pickup_has_iva_and_no_delivery_fee(self):
        t = calculate_totals(Decimal('10000'), 'pickup')
        self.assertEqual(t['delivery_fee'], Decimal('0.00'))
        self.assertEqual(t['tax'], Decimal('1300.00'))
        self.assertEqual(t['total'], Decimal('11300.00'))

    def test_delivery_adds_fee_and_iva_on_fee(self):
        t = calculate_totals(Decimal('10000'), 'delivery')
        self.assertEqual(t['delivery_fee'], Decimal('1500.00'))
        self.assertEqual(t['tax'], Decimal('1495.00'))   # 13 % de 11 500
        self.assertEqual(t['total'], Decimal('12995.00'))


class CardValidatorTests(TestCase):
    def test_expiry_rejects_garbage_without_crashing(self):
        for value in ['ab/cd', '1/2', '', '13/30', '00/30', '12/2']:
            ok, *_ = CardValidator.validate_expiry_date(value)
            self.assertFalse(ok, value)

    def test_expiry_rejects_past_and_absurd_future(self):
        self.assertFalse(CardValidator.validate_expiry_date('01/20')[0])
        self.assertFalse(CardValidator.validate_expiry_date('12/2099')[0])
        self.assertTrue(CardValidator.validate_expiry_date(f'12/{NEXT_YEAR}')[0])

    def test_card_number_rejects_unicode_digits(self):
        self.assertFalse(CardValidator.validate_card_number('４１１１１１１１１１１１１１１１')[0])


class CheckoutFormTests(TestCase):
    def test_valid_pickup(self):
        form = CheckoutForm(valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['customer_phone'], '8888-8888')

    def test_phone_accepts_country_code(self):
        form = CheckoutForm(valid_data(customer_phone='+506 6353 1551'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['customer_phone'], '6353-1551')

    def test_invalid_phone(self):
        for phone in ['1234', '1888-8888', '88888888888']:
            form = CheckoutForm(valid_data(customer_phone=phone))
            self.assertIn('customer_phone', form.errors, phone)

    def test_delivery_requires_address(self):
        form = CheckoutForm(valid_data(fulfillment='delivery'))
        self.assertIn('delivery_address', form.errors)
        form = CheckoutForm(valid_data(fulfillment='delivery',
                                       delivery_address='Cartago, Oreamuno, 200 m norte de la iglesia'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_pickup_discards_address(self):
        form = CheckoutForm(valid_data(delivery_address='Una dirección que no se necesita'))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['delivery_address'], '')

    def test_bad_card_fields(self):
        form = CheckoutForm(valid_data(card_number='4111 1111 1111 1112', expiry_date='99/99', cvv='12'))
        self.assertIn('card_number', form.errors)
        self.assertIn('expiry_date', form.errors)
        self.assertIn('cvv', form.errors)

    def test_amex_needs_four_digit_cvv(self):
        form = CheckoutForm(valid_data(card_number='378282246310005', cvv='123'))
        self.assertIn('cvv', form.errors)
        form = CheckoutForm(valid_data(card_number='378282246310005', cvv='1234'))
        self.assertTrue(form.is_valid(), form.errors)

    def test_sinpe_does_not_need_card(self):
        data = valid_data(payment_method='sinpe', card_number='', card_name='', expiry_date='', cvv='',
                          sinpe_reference='2026 1117 1234')
        form = CheckoutForm(data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['sinpe_reference'], '202611171234')
        self.assertEqual(form.cleaned_data['card_number'], '')

    def test_sinpe_requires_numeric_reference(self):
        for ref in ['', 'ABC123', '123']:
            form = CheckoutForm(valid_data(payment_method='sinpe', sinpe_reference=ref))
            self.assertIn('sinpe_reference', form.errors, ref)

    def test_wallet_requires_token(self):
        form = CheckoutForm(valid_data(payment_method='google_pay', card_number=''))
        self.assertIn('wallet_token', form.errors)
        self.assertTrue(form.non_field_errors())

    def test_google_pay_token_must_be_json(self):
        form = CheckoutForm(valid_data(payment_method='google_pay', wallet_token='{roto'))
        self.assertIn('wallet_token', form.errors)
        form = CheckoutForm(valid_data(payment_method='google_pay', card_number='',
                                       wallet_token='{"signature":"x"}', wallet_description='VISA •••• 1111'))
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.payment_summary, 'Google Pay - VISA •••• 1111')

    def test_card_fields_required_for_card(self):
        form = CheckoutForm(valid_data(card_number='', card_name='', expiry_date='', cvv=''))
        for field in ['card_number', 'card_name', 'expiry_date', 'cvv']:
            self.assertIn(field, form.errors)

    def test_name_rejects_symbols(self):
        form = CheckoutForm(valid_data(customer_name='<script>'))
        self.assertIn('customer_name', form.errors)


@override_settings(IVA_RATE='0.13', DELIVERY_FEE='1500', CAFE_EMAIL='cafe@example.com')
class CheckoutViewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='Cafés', icon='☕')
        self.product = Product.objects.create(name='Latte', description='x', price=Decimal('2000'),
                                              category=category)
        self.cart = Cart.objects.create()
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        session = self.client.session
        session['cart_id'] = self.cart.id
        session.save()
        self.url = reverse('payments:checkout')

    def test_pickup_order_saves_no_personal_data(self):
        response = self.client.post(self.url, valid_data())
        payment = Payment.objects.get()
        self.assertRedirects(response, reverse('payments:success', args=[payment.id]))

        self.assertEqual(payment.fulfillment, 'pickup')
        self.assertEqual(payment.subtotal, Decimal('4000.00'))
        self.assertEqual(payment.tax, Decimal('520.00'))
        self.assertEqual(payment.amount, Decimal('4520.00'))
        self.assertEqual(payment.items.get().quantity, 2)

        # El pedido solo tiene campos de contabilidad: ninguno personal ni de tarjeta
        self.assertEqual(
            {f.name for f in Payment._meta.fields},
            {'id', 'cart', 'fulfillment', 'subtotal', 'tax', 'delivery_fee', 'amount',
             'status', 'payment_method', 'transaction_id', 'reference', 'created_at',
             'invoice_number', 'invoiced_at', 'pending_customer_name', 'pending_customer_email'},
        )
        # Con tarjeta no queda ningún dato de contacto guardado
        self.assertEqual((payment.pending_customer_name, payment.pending_customer_email), ('', ''))
        self.assertRegex(payment.transaction_id, r'^TXN-[0-9A-F]{10}$')

        self.cart.refresh_from_db()
        self.assertFalse(self.cart.is_active)

    def test_delivery_order_totals_and_emails(self):
        address = 'Cartago, Oreamuno, 200 m norte de la iglesia'
        self.client.post(self.url, valid_data(fulfillment='delivery', delivery_address=address))
        payment = Payment.objects.get()
        self.assertEqual(payment.delivery_fee, Decimal('1500.00'))
        self.assertEqual(payment.amount, Decimal('6215.00'))   # (4000 + 1500) * 1.13

        self.assertEqual(len(mail.outbox), 3)   # confirmación, aviso a la cafetería y factura
        to_cafe = next(m for m in mail.outbox if m.to == ['cafe@example.com'])
        self.assertIn(address, to_cafe.body)
        self.assertIn('8888-8888', to_cafe.body)
        for message in mail.outbox:
            self.assertNotIn('4111 1111 1111 1111', message.body)
            self.assertNotIn('4111111111111111', message.body)

    def test_invalid_card_does_not_echo_card_data(self):
        response = self.client.post(self.url, valid_data(card_number='4111 1111 1111 1112'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.exists())
        self.assertNotContains(response, '4111 1111 1111 1112')
        self.assertContains(response, 'maria@example.com')   # los datos de contacto sí se conservan

    def test_double_submit_charges_once(self):
        self.client.post(self.url, valid_data())
        session = self.client.session
        session['cart_id'] = self.cart.id      # simula reenvío con el mismo carrito
        session.save()
        self.client.post(self.url, valid_data())
        self.assertEqual(Payment.objects.count(), 1)

    def test_success_page_only_for_owner_session(self):
        self.client.post(self.url, valid_data())
        payment = Payment.objects.get()
        success = reverse('payments:success', args=[payment.id])
        self.assertEqual(self.client.get(success).status_code, 200)

        other = self.client_class()
        self.assertEqual(other.get(success).status_code, 404)

    def test_sinpe_order_is_pending_with_reference(self):
        self.client.post(self.url, valid_data(payment_method='sinpe', card_number='',
                                              sinpe_reference='202611171234'))
        payment = Payment.objects.get()
        self.assertEqual(payment.payment_method, 'sinpe')
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.reference, '202611171234')
        to_cafe = next(m for m in mail.outbox if m.to == ['cafe@example.com'])
        self.assertIn('verificar el SINPE', to_cafe.body)
        response = self.client.get(reverse('payments:success', args=[payment.id]))
        self.assertContains(response, 'Pedido Recibido')

    def test_apple_pay_order_completed(self):
        self.client.post(self.url, valid_data(payment_method='apple_pay', card_number='',
                                              wallet_token='demo-apple-pay-abc123'))
        payment = Payment.objects.get()
        self.assertEqual((payment.payment_method, payment.status), ('apple_pay', 'completed'))
        self.assertEqual(payment.reference, '')

    def test_checkout_page_lists_all_methods(self):
        response = self.client.get(self.url)
        for label in ['Tarjeta', 'SINPE Móvil', 'Google Pay', 'Apple Pay', '6353-1551']:
            self.assertContains(response, label)

    def test_card_payment_sends_invoice_to_customer(self):
        self.client.post(self.url, valid_data())
        payment = Payment.objects.get()
        self.assertTrue(payment.invoice_number.startswith('FAC-'))
        self.assertIsNotNone(payment.invoiced_at)

        invoice = next(m for m in mail.outbox if m.subject.startswith('Factura'))
        self.assertEqual(invoice.to, ['maria@example.com'])
        self.assertIn(payment.invoice_number, invoice.body)
        self.assertIn('Visa terminada en 1111', invoice.body)
        self.assertIn('₡4520', invoice.body)
        html, mimetype = invoice.alternatives[0]
        self.assertEqual(mimetype, 'text/html')
        self.assertIn('María Pérez', html)
        confirmation = next(m for m in mail.outbox if m.subject.startswith('Pedido confirmado'))
        self.assertEqual(confirmation.to, ['maria@example.com'])

    def _sinpe_order(self):
        self.client.post(self.url, valid_data(payment_method='sinpe', card_number='',
                                              sinpe_reference='202611171234'))
        mail.outbox.clear()
        return Payment.objects.get()

    def test_sinpe_keeps_contact_only_until_invoice(self):
        payment = self._sinpe_order()
        self.assertEqual(payment.pending_customer_email, 'maria@example.com')
        self.assertEqual(payment.invoice_number, '')

        from .invoices import confirm_sinpe
        self.assertTrue(confirm_sinpe(payment))
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        self.assertTrue(payment.invoice_number)
        self.assertEqual((payment.pending_customer_name, payment.pending_customer_email), ('', ''))
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['maria@example.com'])
        self.assertIn('comprobante 202611171234', mail.outbox[0].body)

        # Confirmar otra vez no reenvía la factura
        self.assertFalse(confirm_sinpe(payment))
        self.assertEqual(len(mail.outbox), 1)

    def test_sinpe_reject_notifies_and_forgets_contact(self):
        payment = self._sinpe_order()
        from .invoices import reject_sinpe
        reject_sinpe(payment)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'failed')
        self.assertEqual(payment.pending_customer_email, '')
        self.assertEqual(mail.outbox[0].to, ['maria@example.com'])
        self.assertIn('No pudimos verificar', mail.outbox[0].subject)

    def test_admin_status_change_sends_invoice(self):
        from django.contrib.auth.models import User
        payment = self._sinpe_order()
        admin_user = User.objects.create_superuser('admin_test', 'a@example.com', 'clave-segura-123')
        self.client.force_login(admin_user)
        response = self.client.post(reverse('admin:payments_payment_changelist'), {
            'action': 'confirm_sinpe_action', '_selected_action': [payment.id],
        })
        self.assertEqual(response.status_code, 302)
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'completed')
        self.assertEqual([m.to for m in mail.outbox], [['maria@example.com']])

    def test_cart_page_shows_iva(self):
        response = self.client.get(reverse('cart:cart'))
        self.assertContains(response, 'IVA (13%)')
        self.assertContains(response, '₡4520')

    def test_cart_quantity_garbage_does_not_crash(self):
        item = self.cart.items.get()
        response = self.client.post(reverse('cart:update_cart', args=[item.id]), {'quantity': 'abc'})
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
