import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters

from cart.models import Cart

from .forms import SINPE, CheckoutForm
from .invoices import send_invoice
from .models import Payment, PaymentItem
from .pricing import DELIVERY, calculate_totals, delivery_fee

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
    se usan para validar y para los correos, y no se guardan (salvo el
    nombre y correo de un SINPE pendiente, hasta enviar su factura).
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
            # Solo SINPE: la factura se envía después de verificar el depósito,
            # así que el contacto se guarda hasta entonces (luego se borra).
            pending_customer_name=form.cleaned_data['customer_name'] if method == SINPE else '',
            pending_customer_email=form.cleaned_data['customer_email'] if method == SINPE else '',
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
    """Envía los correos al cliente y a la cafetería.

    Es el único lugar donde se usan los datos personales; no se guardan.
    """
    data = form.cleaned_data
    metodo_pago = form.payment_summary
    is_sinpe = payment.payment_method == SINPE
    is_delivery = payment.fulfillment == DELIVERY
    fecha = timezone.localtime(payment.created_at).strftime('%d/%m/%Y %H:%M')

    productos = "\n".join(
        f"   {item.quantity}x {item.product_name} - {_colones(item.get_subtotal())}"
        for item in payment.items.all()
    )
    resumen = (
        f"   Subtotal: {_colones(payment.subtotal)}\n"
        + (f"   Envío a domicilio: {_colones(payment.delivery_fee)}\n" if is_delivery else "")
        + f"   IVA (13%): {_colones(payment.tax)}\n"
        f"   TOTAL PAGADO: {_colones(payment.amount)}"
    )
    if is_delivery:
        entrega = f"ENTREGA A DOMICILIO\n   Dirección: {data['delivery_address']}"
        if data.get('delivery_notes'):
            entrega += f"\n   Indicaciones: {data['delivery_notes']}"
    else:
        entrega = "RECOGER EN TIENDA\n   Te avisaremos cuando tu pedido esté listo."

    if is_sinpe:
        estado_cliente = ("Recibimos tu pedido. Lo confirmaremos en cuanto verifiquemos "
                          "el SINPE Móvil con el comprobante que indicaste;\n"
                          "en ese momento te enviaremos la factura a este correo.")
        accion_cafe = ("\n>>> ACCIÓN: verificar el SINPE con ese comprobante y marcar el pago "
                       "como Completado en el admin.\n")
    else:
        estado_cliente = "Tu pedido fue confirmado. La factura te llega en un correo aparte."
        accion_cafe = ""

    mensaje_cliente = f"""Hola {data['customer_name']},

Gracias por tu compra en Cafetería Irazú. {estado_cliente}

PRODUCTOS:
{productos}

RESUMEN DE PAGO:
{resumen}

{entrega}

Fecha: {fecha}
Transacción: {payment.transaction_id}
Pago: {metodo_pago}

Por tu privacidad, no guardamos tus datos personales ni los de tu medio de pago.

Cafetería Irazú - Cartago, Costa Rica
Teléfono: 6353-1551
"""

    mensaje_cafe = f"""NUEVO PEDIDO - {payment.get_fulfillment_display().upper()}

CLIENTE:
   Nombre: {data['customer_name']}
   Correo: {data['customer_email']}
   Teléfono: {data['customer_phone']}

{entrega}

PRODUCTOS:
{productos}

RESUMEN:
{resumen}

Fecha: {fecha}
Transacción: {payment.transaction_id}
Pago: {metodo_pago}
{accion_cafe}
Los datos del cliente solo aparecen en este correo; el sistema no los guarda.
"""

    envios = [
        (f'Pedido confirmado - {payment.transaction_id}', mensaje_cliente, data['customer_email']),
        (f'NUEVO PEDIDO {payment.transaction_id} - {payment.get_fulfillment_display()} - '
         f'{_colones(payment.amount)}', mensaje_cafe, settings.CAFE_EMAIL),
    ]
    for subject, body, recipient in envios:
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient])
        except Exception:
            # No se registra el destinatario para no dejar datos personales en los logs
            logger.exception("No se pudo enviar el correo del pedido %s", payment.transaction_id)


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
