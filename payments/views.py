# D:\cafeteria_irazu_proyecto\cafeteria_irazu\payments\views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from decimal import Decimal
from cart.models import Cart
from .forms import PaymentForm
from .models import Payment, PaymentItem

def checkout(request):
    cart_id = request.session.get('cart_id')
    cart = get_object_or_404(Cart, id=cart_id, is_active=True) if cart_id else None
    
    if not cart or cart.items.count() == 0:
        messages.warning(request, 'Tu carrito está vacío')
        return redirect('cart:cart')
    
    # Calcular total con servicio (10%) - CORREGIDO
    subtotal = cart.get_total()
    service_charge = subtotal * Decimal('0.10')  # Usar Decimal en lugar de float
    total = subtotal + service_charge
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Simular validación de tarjeta
            card_number = form.cleaned_data['card_number'].replace(' ', '')
            card_name = form.cleaned_data['card_name']
            expiry = form.cleaned_data['expiry_date']
            cvv = form.cleaned_data['cvv']
            
            # Validaciones básicas de tarjeta
            errors = []
            if len(card_number) < 15:
                errors.append("Número de tarjeta inválido")
            if len(cvv) < 3:
                errors.append("CVV inválido")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, 'payments/checkout.html', {
                    'form': form,
                    'cart': cart,
                    'subtotal': subtotal,
                    'service_charge': service_charge,
                    'total': total
                })
            
            # Crear pago
            payment = form.save(commit=False)
            payment.cart = cart
            payment.amount = total
            payment.status = 'completed'
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
            
            messages.success(request, f'✅ Pago exitoso! Transacción: {payment.transaction_id}')
            return redirect('payments:success', payment_id=payment.id)
    else:
        form = PaymentForm()
    
    return render(request, 'payments/checkout.html', {
        'form': form,
        'cart': cart,
        'subtotal': subtotal,
        'service_charge': service_charge,
        'total': total
    })

def payment_success(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    return render(request, 'payments/success.html', {'payment': payment})