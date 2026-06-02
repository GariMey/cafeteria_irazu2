# payments/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from cart.models import Cart
from .forms import PaymentForm
from .models import Payment, PaymentItem
from .card_validator import CardValidator


def checkout(request):
    """
    Vista principal del proceso de pago.
    Valida los datos de la tarjeta sin hacer cargos reales.
    """
    cart_id = request.session.get('cart_id')
    cart = None
    
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id, is_active=True)
        except Cart.DoesNotExist:
            pass
    
    # Verificar que el carrito existe y tiene items
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Tu carrito esta vacio')
        return redirect('cart:cart')
    
    # Calcular totales
    subtotal = cart.get_total()
    service_charge = subtotal * Decimal('0.10')
    total = subtotal + service_charge
    
    if request.method == 'POST':
        # Obtener datos del formulario
        card_number = request.POST.get('card_number', '').strip()
        card_name = request.POST.get('card_name', '').strip()
        expiry_date = request.POST.get('expiry_date', '').strip()
        cvv = request.POST.get('cvv', '').strip()
        customer_name = request.POST.get('customer_name', '').strip()
        customer_email = request.POST.get('customer_email', '').strip()
        customer_phone = request.POST.get('customer_phone', '').strip()
        
        # Validar campos obligatorios
        if not all([card_number, card_name, expiry_date, cvv, customer_name, customer_email]):
            messages.error(request, 'Por favor complete todos los campos obligatorios')
            return render(request, 'payments/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'service_charge': service_charge,
                'total': total,
                'form_data': request.POST
            })
        

        # VALIDACION REAL DE LA TARJETA
     
        is_valid, error_msg, card_data = CardValidator.validate_card(
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            cardholder_name=card_name
        )
        
        if not is_valid:
            messages.error(request, f'Error en la tarjeta: {error_msg}')
            return render(request, 'payments/checkout.html', {
                'cart': cart,
                'subtotal': subtotal,
                'service_charge': service_charge,
                'total': total,
                'form_data': request.POST
            })
        
        
        # TARJETA VALIDA - PROCESAR PAGO SIMULADO
        
        
        # Crear registro de pago
        payment = Payment.objects.create(
            cart=cart,
            amount=total,
            status='completed',
            payment_method='card',
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone or 'No especificado'
        )
        
        # Guardar informacion de la tarjeta (solo ultimos 4 digitos y marca)
        payment.transaction_id = f"TXN-{payment.id:06d}"
        payment.save()
        
        # Guardar items del pago
        for item in cart.items.all():
            PaymentItem.objects.create(
                payment=payment,
                product_name=item.product.name,
                quantity=item.quantity,
                price=item.product.price
            )
        
        # Limpiar carrito
        cart.is_active = False
        cart.save()
        request.session['cart_id'] = None
        
        # Mostrar mensaje con informacion de la tarjeta valida
        messages.success(
            request,
            f'Pago exitoso. Tarjeta {card_data["brand"]} terminada en {card_data["last_four"]}. Transaccion: {payment.transaction_id}'
        )
        
       
        # ENVIO DE EMAILS
        
        
        # Obtener los items del pedido para los emails
        payment_items = PaymentItem.objects.filter(payment=payment)
        
        # Construir lista de productos para emails
        productos_texto = ""
        for item in payment_items:
            productos_texto += f"   {item.quantity}x {item.product_name} - ${item.price * item.quantity:,.0f}\n"
        
        # 1. EMAIL PARA EL CLIENTE
        try:
            mensaje_cliente = f"""
Hola {payment.customer_name},

Gracias por tu compra en Cafeteria Irazu. Tu pedido ha sido confirmado.

DETALLES DEL PEDIDO:
{productos_texto}

RESUMEN DE PAGO:
   Subtotal: ${subtotal:,.0f}
   Servicio (10 por ciento): ${service_charge:,.0f}
   TOTAL PAGADO: ${payment.amount:,.0f}

Fecha: {payment.created_at.strftime('%d/%m/%Y %H:%M')}
Transaccion: {payment.transaction_id}
Tarjeta: {card_data['brand']} terminada en {card_data['last_four']}

Te esperamos en Cafeteria Irazu.

Direccion:Cartago, Costa Rica
Telefono: 6353-1551

Cafeteria Irazu - Cartago, Costa Rica
            """
            
            send_mail(
                subject=f'Pedido Confirmado - #{payment.transaction_id}',
                message=mensaje_cliente,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[payment.customer_email],
                fail_silently=True,
            )
            print(f"Email de confirmacion enviado a {payment.customer_email}")
        except Exception as e:
            print(f"Error al enviar email al cliente: {e}")
        
        # 2. EMAIL PARA EL DUENO DEL CAFE
        try:
            productos_texto_admin = ""
            for item in payment_items:
                productos_texto_admin += f"   - {item.quantity}x {item.product_name} - ${item.price * item.quantity:,.0f}\n"
            
            mensaje_admin = f"""
NUEVO PEDIDO RECIBIDO

DATOS DEL CLIENTE:
   Nombre: {payment.customer_name}
   Email: {payment.customer_email}
   Telefono: {payment.customer_phone}

PRODUCTOS DEL PEDIDO:
{productos_texto_admin}

TOTAL DEL PEDIDO: ${payment.amount:,.0f}

Fecha: {payment.created_at.strftime('%d/%m/%Y %H:%M')}
Transaccion: {payment.transaction_id}
Tarjeta: {card_data['brand']} terminada en {card_data['last_four']}

Para ver mas detalles, ingrese al panel de administracion.
            """
            
            send_mail(
                subject=f'NUEVO PEDIDO - {payment.customer_name} - ${payment.amount:,.0f}',
                message=mensaje_admin,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CAFE_EMAIL],
                fail_silently=True,
            )
            print(f"Notificacion enviada al dueno: {settings.CAFE_EMAIL}")
        except Exception as e:
            print(f"Error al enviar email al dueno: {e}")
        
        return redirect('payments:success', payment_id=payment.id)
    
    # GET request - mostrar formulario
    return render(request, 'payments/checkout.html', {
        'cart': cart,
        'subtotal': subtotal,
        'service_charge': service_charge,
        'total': total
    })


def payment_success(request, payment_id):
    """
    Vista que se muestra despues de un pago exitoso.
    """
    payment = get_object_or_404(Payment, id=payment_id)
    payment_items = PaymentItem.objects.filter(payment=payment)
    
    # Calcular subtotal y servicio para mostrar
    subtotal = payment.amount / Decimal('1.10')
    service_charge = payment.amount - subtotal
    
    context = {
        'payment': payment,
        'payment_items': payment_items,
        'subtotal': subtotal,
        'service_charge': service_charge,
        'total': payment.amount,
    }
    
    return render(request, 'payments/success.html', context)