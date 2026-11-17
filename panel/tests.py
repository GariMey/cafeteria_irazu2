from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from cafeteria.models import Category, ContactMessage, Product
from payments.models import Payment, PaymentItem


def make_order(**kwargs):
    data = dict(amount=Decimal('4520'), subtotal=Decimal('4000'), tax=Decimal('520'),
                status='completed', payment_method='card', contact_name='María Pérez',
                contact_email='maria@example.com', contact_phone='8888-8888')
    data.update(kwargs)
    payment = Payment.objects.create(**data)
    PaymentItem.objects.create(payment=payment, product_name='Latte', quantity=2, price=Decimal('2000'))
    return payment


@override_settings(CAFE_EMAIL='cafe@example.com')
class PanelTestCase(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user('cafeteria', password='clave-segura-123', is_staff=True)
        self.client.force_login(self.staff)


class AccessTests(TestCase):
    def test_anonymous_is_sent_to_login(self):
        response = self.client.get(reverse('panel:orders'))
        self.assertRedirects(response, f"{reverse('panel:login')}?next={reverse('panel:orders')}")

    def test_customer_account_cannot_enter(self):
        User.objects.create_user('cliente', password='clave-segura-123')
        response = self.client.post(reverse('panel:login'),
                                    {'username': 'cliente', 'password': 'clave-segura-123'})
        self.assertContains(response, 'no tiene acceso al panel')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_staff_can_log_in(self):
        User.objects.create_user('cafeteria', password='clave-segura-123', is_staff=True)
        response = self.client.post(reverse('panel:login'),
                                    {'username': 'cafeteria', 'password': 'clave-segura-123'})
        self.assertRedirects(response, reverse('panel:orders'))


class OrderPanelTests(PanelTestCase):
    def test_lists_active_orders_with_contact(self):
        make_order()
        response = self.client.get(reverse('panel:orders'))
        self.assertContains(response, 'María Pérez')
        self.assertContains(response, 'Empezar a preparar')

    def test_partial_refresh(self):
        make_order()
        response = self.client.get(reverse('panel:orders'), HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'id="orders-list"')
        self.assertNotContains(response, '<html')

    def _act(self, order, **data):
        return self.client.post(reverse('panel:order_action', args=[order.pk]), data)

    def test_pickup_flow_and_contact_deleted_on_delivery(self):
        order = make_order()
        for status in ['preparing', 'ready', 'delivered']:
            self._act(order, action='advance', to=status)
            order.refresh_from_db()
            self.assertEqual(order.order_status, status)
        self.assertFalse(order.has_contact)

    def test_delivery_goes_on_the_way_not_ready(self):
        order = make_order(fulfillment='delivery', delivery_address='Cartago centro, 100 m sur')
        self._act(order, action='advance', to='preparing')
        self._act(order, action='advance', to='ready')          # no aplica a domicilio
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'preparing')
        self._act(order, action='advance', to='on_the_way')
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'on_the_way')
        self.assertEqual(order.delivery_address, 'Cartago centro, 100 m sur')

    def test_cancel_refunds_and_forgets_contact(self):
        order = make_order()
        self._act(order, action='cancel')
        order.refresh_from_db()
        self.assertEqual((order.order_status, order.status), ('cancelled', 'refunded'))
        self.assertFalse(order.has_contact)

    def test_sinpe_must_be_confirmed_before_preparing(self):
        order = make_order(status='pending', payment_method='sinpe', reference='123456789')
        self._act(order, action='advance', to='preparing')
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'new')

        self._act(order, action='confirm_sinpe')
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertTrue(order.invoice_number)
        self.assertEqual(mail.outbox[0].to, ['maria@example.com'])

    def test_sinpe_reject_cancels(self):
        order = make_order(status='pending', payment_method='sinpe', reference='123456789')
        self._act(order, action='reject_sinpe')
        order.refresh_from_db()
        self.assertEqual((order.order_status, order.status), ('cancelled', 'failed'))
        self.assertFalse(order.has_contact)

    def test_old_open_orders_lose_contact(self):
        order = make_order()
        Payment.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=30))
        self.client.get(reverse('panel:orders'))
        order.refresh_from_db()
        self.assertFalse(order.has_contact)

    def test_orders_need_post(self):
        order = make_order()
        response = self.client.get(reverse('panel:order_action', args=[order.pk]))
        self.assertEqual(response.status_code, 405)


class ProductPanelTests(PanelTestCase):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(name='Cafés', icon='☕')

    def test_create_and_edit_product(self):
        response = self.client.post(reverse('panel:product_new'), {
            'name': '  Té   Chai ', 'category': self.category.pk, 'description': 'Especiado',
            'price': '2500', 'available': 'on',
        })
        self.assertRedirects(response, reverse('panel:products'))
        product = Product.objects.get()
        self.assertEqual(product.name, 'Té Chai')

        self.client.post(reverse('panel:product_edit', args=[product.pk]), {
            'name': 'Té Chai', 'category': self.category.pk, 'description': 'Especiado',
            'price': '2800', 'available': 'on', 'featured': 'on',
        })
        product.refresh_from_db()
        self.assertEqual((product.price, product.featured), (Decimal('2800'), True))

    def test_price_must_be_positive(self):
        response = self.client.post(reverse('panel:product_new'), {
            'name': 'Gratis', 'category': self.category.pk, 'description': 'x', 'price': '0',
        })
        self.assertContains(response, 'mayor que cero')
        self.assertFalse(Product.objects.exists())

    def test_toggle_available_and_safe_redirect(self):
        product = Product.objects.create(name='Latte', description='x', price=2000, category=self.category)
        response = self.client.post(reverse('panel:product_toggle', args=[product.pk]),
                                    {'field': 'available', 'next': 'https://sitio-malo.com/'})
        self.assertRedirects(response, reverse('panel:products'))
        product.refresh_from_db()
        self.assertFalse(product.available)

    def test_delete_product(self):
        product = Product.objects.create(name='Latte', description='x', price=2000, category=self.category)
        self.client.post(reverse('panel:product_delete', args=[product.pk]))
        self.assertFalse(Product.objects.exists())


class InboxPanelTests(PanelTestCase):
    def setUp(self):
        super().setUp()
        self.msg = ContactMessage.objects.create(name='Ana', email='ana@example.com',
                                                 message='¿Tienen opciones veganas?')

    def test_opening_marks_as_read(self):
        self.client.get(reverse('panel:message', args=[self.msg.pk]))
        self.msg.refresh_from_db()
        self.assertTrue(self.msg.read)

    def test_reply_sends_email_to_customer(self):
        response = self.client.post(reverse('panel:message', args=[self.msg.pk]), {
            'subject': 'Re: Tu mensaje', 'body': 'Hola Ana, sí tenemos leche de avena.',
        })
        self.assertRedirects(response, reverse('panel:message', args=[self.msg.pk]))
        email = mail.outbox[0]
        self.assertEqual(email.to, ['ana@example.com'])
        self.assertEqual(email.reply_to, ['cafe@example.com'])
        self.assertIn('leche de avena', email.body)
        self.assertIn('> ¿Tienen opciones veganas?', email.body)
        self.msg.refresh_from_db()
        self.assertIsNotNone(self.msg.replied_at)

    def test_unread_filter(self):
        ContactMessage.objects.create(name='Leído', email='l@example.com', message='x', read=True)
        response = self.client.get(reverse('panel:inbox') + '?ver=sin-leer')
        self.assertContains(response, 'Ana')
        self.assertNotContains(response, 'Leído')


# ── Galería y La Experiencia ───────────────────────────────────────────────
import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from cafeteria.models import ExperienceFeature, GalleryImage

TEMP_MEDIA = tempfile.mkdtemp()
# Nunca subir a Cloudinary durante las pruebas: se guarda en una carpeta temporal
LOCAL_STORAGE = override_settings(
    MEDIA_ROOT=TEMP_MEDIA,
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)


def fake_image(name='foto.jpg', size=(40, 30)):
    buffer = io.BytesIO()
    Image.new('RGB', size, (196, 149, 106)).save(buffer, 'JPEG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')


@LOCAL_STORAGE
class GalleryPanelTests(PanelTestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def test_upload_several_photos_at_once(self):
        response = self.client.post(reverse('panel:gallery'),
                                    {'images': [fake_image('a.jpg'), fake_image('b.jpg')]})
        self.assertRedirects(response, reverse('panel:gallery'))
        self.assertEqual(GalleryImage.objects.count(), 2)
        self.assertEqual(list(GalleryImage.objects.values_list('order', flat=True)), [1, 2])

    def test_rejects_files_that_are_not_images(self):
        fake = SimpleUploadedFile('virus.jpg', b'esto no es una imagen', content_type='image/jpeg')
        response = self.client.post(reverse('panel:gallery'), {'images': [fake]})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GalleryImage.objects.exists())

    def test_edit_and_delete_photo(self):
        image = GalleryImage.objects.create(image=fake_image(), order=5)
        prefix = f'img{image.pk}'
        self.client.post(reverse('panel:gallery_update', args=[image.pk]),
                         {f'{prefix}-title': 'Terraza', f'{prefix}-order': '1'})
        image.refresh_from_db()
        self.assertEqual((image.title, image.order), ('Terraza', 1))

        self.client.post(reverse('panel:gallery_delete', args=[image.pk]))
        self.assertFalse(GalleryImage.objects.exists())

    def test_gallery_page_renders(self):
        GalleryImage.objects.create(image=fake_image(), order=1, title='Fachada')
        self.assertContains(self.client.get(reverse('panel:gallery')), 'Fachada')


@LOCAL_STORAGE
class ExperiencePanelTests(PanelTestCase):
    def test_existing_cards_were_loaded(self):
        titles = list(ExperienceFeature.objects.values_list('title', flat=True))
        self.assertEqual(len(titles), 6)
        self.assertIn('Pet Friendly', titles)
        self.assertTrue(ExperienceFeature.objects.get(title='Parqueo Amplio').image_url.endswith('Parking.jpg'))

    def test_edit_card_with_new_image(self):
        feature = ExperienceFeature.objects.get(title='Pet Friendly')
        response = self.client.post(reverse('panel:experience_edit', args=[feature.pk]), {
            'icon': '🐶', 'title': 'Mascotas bienvenidas', 'description': 'Traé a tu perro.',
            'order': '2', 'active': 'on', 'image': fake_image('perro.jpg'),
        })
        self.assertRedirects(response, reverse('panel:experience'))
        feature.refresh_from_db()
        self.assertEqual(feature.title, 'Mascotas bienvenidas')
        self.assertTrue(feature.image.name.startswith('experience/'))

        home = self.client.get(reverse('home'))
        self.assertContains(home, 'Mascotas bienvenidas')
        self.assertContains(home, feature.image.url)

    def test_hidden_card_not_on_home(self):
        ExperienceFeature.objects.filter(title='Música Agradable').update(active=False)
        home = self.client.get(reverse('home'))
        self.assertNotContains(home, 'Música Agradable')
        self.assertContains(home, 'Vista a las Montañas')

    def test_create_and_delete_card(self):
        self.client.post(reverse('panel:experience_new'), {
            'icon': '📶', 'title': 'WiFi gratis', 'description': 'Conexión rápida para trabajar.',
            'order': '7', 'active': 'on',
        })
        feature = ExperienceFeature.objects.get(title='WiFi gratis')
        self.assertEqual(feature.image_url, '')
        self.client.post(reverse('panel:experience_delete', args=[feature.pk]))
        self.assertFalse(ExperienceFeature.objects.filter(title='WiFi gratis').exists())


# ── Reservas ───────────────────────────────────────────────────────────────
from datetime import date, time

from bookings.models import Reservation, Table


class ReservationPanelTests(PanelTestCase):
    def setUp(self):
        super().setUp()
        self.today = timezone.localdate()
        self.res = Reservation.objects.create(
            customer_name='Ana Mora', customer_email='ana@example.com', customer_phone='8888-8888',
            date=self.today + timedelta(days=1), time=time(18, 0), guests=4,
            special_requests='Mesa en la terraza')
        self.table = Table.objects.get(number=1)   # creada por la migración 0003

    def _act(self, **data):
        return self.client.post(reverse('panel:reservation_action', args=[self.res.pk]), data)

    def test_migration_created_tables(self):
        self.assertEqual(Table.objects.count(), 14)

    def test_upcoming_list_shows_reservation_and_counter(self):
        response = self.client.get(reverse('panel:reservations'))
        self.assertContains(response, 'Ana Mora')
        self.assertContains(response, 'Mesa en la terraza')
        self.assertEqual(response.context['counters']['pending_reservations'], 1)

    def test_confirm_sends_email(self):
        self._act(action='confirm')
        self.res.refresh_from_db()
        self.assertEqual(self.res.status, 'confirmed')
        self.assertEqual(mail.outbox[0].to, ['ana@example.com'])
        self.assertIn('confirmada', mail.outbox[0].subject)

    def test_complete_only_after_confirm(self):
        self._act(action='complete')
        self.res.refresh_from_db()
        self.assertEqual(self.res.status, 'pending')
        self._act(action='confirm')
        self._act(action='complete')
        self.res.refresh_from_db()
        self.assertEqual(self.res.status, 'completed')

    def test_cancel_with_and_without_notice(self):
        self._act(action='cancel', notify='0')
        self.res.refresh_from_db()
        self.assertEqual(self.res.status, 'cancelled')
        self.assertEqual(len(mail.outbox), 0)

        other = Reservation.objects.create(customer_name='Luis', customer_email='luis@example.com',
                                           customer_phone='7777-7777', date=self.res.date,
                                           time=time(12, 0), guests=2)
        self.client.post(reverse('panel:reservation_action', args=[other.pk]),
                         {'action': 'cancel', 'notify': '1'})
        self.assertEqual(mail.outbox[0].to, ['luis@example.com'])

    def test_assign_table_and_detect_conflict(self):
        self._act(action='table', table=self.table.pk)
        self.res.refresh_from_db()
        self.assertEqual(self.res.table, self.table)

        clash = Reservation.objects.create(customer_name='Otro', customer_email='o@example.com',
                                           customer_phone='6666-6666', date=self.res.date,
                                           time=time(19, 0), guests=2)
        response = self.client.post(reverse('panel:reservation_action', args=[clash.pk]),
                                    {'action': 'table', 'table': self.table.pk}, follow=True)
        clash.refresh_from_db()
        self.assertIsNone(clash.table)
        self.assertContains(response, 'ya está reservada')

    def test_small_table_warns(self):
        self.res.guests = 8
        self.res.save()
        response = self._act(action='table', table=self.table.pk)
        self.res.refresh_from_db()
        self.assertEqual(self.res.table, self.table)
        response = self.client.get(reverse('panel:reservations'))
        self.assertContains(response, 'Mesa 1')

    def test_today_filter(self):
        Reservation.objects.create(customer_name='Hoy Persona', customer_email='h@example.com',
                                   customer_phone='8888-0000', date=self.today, time=time(9, 0), guests=2)
        response = self.client.get(reverse('panel:reservations') + '?ver=hoy')
        self.assertContains(response, 'Hoy Persona')
        self.assertNotContains(response, 'Ana Mora')
