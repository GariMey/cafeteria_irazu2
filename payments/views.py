import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters

from cafeteria.emails import try_send_branded
from cart.models import Cart

from .forms import SINPE, CheckoutForm
from .invoices import send_invoice
from .models import Payment, PaymentItem
from .pricing import DELIVERY, calculate_totals, delivery_fee, iva_rate

logger = logging.getLogger(__name__)

# Pedidos que esta sesión puede ver en la página de confirmación
SESSION_ORDERS_KEY = 'paid_orders'

SENSITIVE_FIELDS = (
    'card_number', 'card_name', 'expiry_date', 'cvv', 'wallet_token', 'wallet_description',
    'customer_name', 'customer_email', 'customer_phone',
    'delivery_address', 'delivery_notes',
)


def _active_cart(request):
    cart_id = request.session.get('cart_id')
    if not cart_id:
        return None
    return Cart.objects.filter(id=cart_id, is_active=True).first()


def _colones(value):
    return f"₡{value:,.0f}"


@sensitive_post_parameters(*SENSITIVE_FIELDS)
def checkout(request):
    """Pago simulado con tarjeta, SINPE Móvil, Google Pay o Apple Pay.

    Ningún método realiza cargos reales. Tarjeta y billeteras quedan como
    pagadas; SINPE queda pendiente hasta que la cafetería verifique el
    comprobante en el admin.

    Los datos personales y de tarjeta solo viven durante esta petición:
    la tarjeta nunca se guarda; el contacto se guarda solo mientras el
    pedido está activo y se borra al entregarlo o cancelarlo.
    """
    cart = _active_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('cart:cart')

    form = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        payment = _process_order(request, cart, form)
        if payment is None:
            # El carrito ya se había pagado (doble clic / reenvío del formulario)
            messages.info(request, 'Este pedido ya fue procesado.')
            return redirect('cart:cart')

        _send_confirmation_emails(payment, form)
        # Pago ya confirmado (tarjeta / billeteras): la factura sale de inmediato
        send_invoice(payment, form.cleaned_data['customer_name'],
                     form.cleaned_data['customer_email'], form.payment_summary)

        # Solo esta sesión podrá ver la confirmación de este pedido
        orders = request.session.get(SESSION_ORDERS_KEY, [])[-9:]
        request.session[SESSION_ORDERS_KEY] = orders + [payment.id]
        request.session['cart_id'] = None
        return redirect('payments:success', payment_id=payment.id)

    if request.method == 'POST':
        form.clear_secret_data()
        messages.error(request, 'Revisa los campos marcados en rojo.')

    fulfillment = form.data.get('fulfillment') if form.is_bound else form.fields['fulfillment'].initial
    return render(request, 'payments/checkout.html', {
        'cart': cart,
        'form': form,
        'totals': calculate_totals(cart.get_total(), fulfillment),
        'pickup_totals': calculate_totals(cart.get_total(), 'pickup'),
        'delivery_totals': calculate_totals(cart.get_total(), DELIVERY),
        'delivery_fee': delivery_fee(),
        'sinpe_number': settings.SINPE_NUMBER,
        'sinpe_holder': settings.SINPE_HOLDER,
        'google_pay_environment': settings.GOOGLE_PAY_ENVIRONMENT,
    })


def _process_order(request, cart, form):
    """Registra el pedido de forma atómica. Devuelve None si ya estaba pagado."""
    with transaction.atomic():
        # Bloquea el carrito para que dos envíos simultáneos no cobren dos veces
        locked = Cart.objects.select_for_update().filter(id=cart.id, is_active=True).first()
        if locked is None:
            return None

        items = list(locked.items.select_related('product'))
        totals = calculate_totals(locked.get_total(), form.cleaned_data['fulfillment'])
        method = form.cleaned_data['payment_method']

        payment = Payment.objects.create(
            cart=locked,
            fulfillment=form.cleaned_data['fulfillment'],
            subtotal=totals['subtotal'],
            tax=totals['tax'],
            delivery_fee=totals['delivery_fee'],
            amount=totals['total'],
            # SINPE se confirma manualmente al ver el depósito; lo demás es inmediato
            status='pending' if method == SINPE else 'completed',
            payment_method=method,
            reference=form.cleaned_data.get('sinpe_reference', ''),
            # Contacto temporal para preparar/entregar el pedido y enviar la
            # factura; se borra al entregarlo o cancelarlo (payments.orders).
            contact_name=form.cleaned_data['customer_name'],
            contact_email=form.cleaned_data['customer_email'],
            contact_phone=form.cleaned_data['customer_phone'],
            delivery_address=form.cleaned_data['delivery_address'],
            delivery_notes=form.cleaned_data['delivery_notes'],
        )
        PaymentItem.objects.bulk_create([
            PaymentItem(payment=payment, product_name=item.product.name,
                        quantity=item.quantity, price=item.product.price)
            for item in items
        ])

        locked.is_active = False
        locked.save(update_fields=['is_active', 'updated_at'])
    return payment


def _send_confirmation_emails(payment, form):
    """Envía la confirmación al cliente y el aviso de nuevo pedido a la cafetería.

    Los datos de contacto vienen del formulario; nunca se registran en los logs.
    """
    data = form.cleaned_data
    is_sinpe = payment.payment_method == SINPE
    fecha = timezone.localtime(payment.created_at).strftime('%d/%m/%Y %H:%M')
    context = {
        'payment': payment,
        'items': list(payment.items.all()),
        'is_delivery': payment.fulfillment == DELIVERY,
        'is_sinpe': is_sinpe,
        'tax_percent': int(iva_rate() * 100),
        'customer_name': data['customer_name'],
        'delivery_address': data.get('delivery_address', ''),
        'delivery_notes': data.get('delivery_notes', ''),
    }
    reference = f"el pedido {payment.transaction_id}"

    try_send_branded(
        f'Pedido confirmado - {payment.transaction_id}', 'order_confirmation',
        {**context, 'rows': [('Pedido', payment.transaction_id), ('Fecha', fecha),
                             ('Pago', form.payment_summary),
                             ('Entrega', payment.get_fulfillment_display())]},
        [data['customer_email']], reference=reference,
    )
    try_send_branded(
        f'NUEVO PEDIDO {payment.transaction_id} - {payment.get_fulfillment_display()} - '
        f'{_colones(payment.amount)}', 'order_new_cafe',
        {**context, 'rows': [('Cliente', data['customer_name']), ('Teléfono', data['customer_phone']),
                             ('Correo', data['customer_email']), ('Fecha', fecha),
                             ('Pago', form.payment_summary)]},
        [settings.CAFE_EMAIL], reference=reference,
        # Responder a este aviso le escribe directamente al cliente
        reply_to=[data['customer_email']],
    )


def payment_success(request, payment_id):
    """Confirmación del pedido. Solo la sesión que pagó puede verla."""
    if payment_id not in request.session.get(SESSION_ORDERS_KEY, []):
        raise Http404("Pedido no encontrado")

    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'payments/success.html', {
        'payment': payment,
        'payment_items': payment.items.all(),
        'is_delivery': payment.fulfillment == DELIVERY,
        'is_sinpe': payment.payment_method == SINPE,
    })
