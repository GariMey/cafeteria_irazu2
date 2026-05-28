from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from cafeteria.models import Product
from .models import Cart, CartItem

def get_or_create_cart(request):
    cart_id = request.session.get('cart_id')
    
    if cart_id:
        try:
            return Cart.objects.get(id=cart_id, is_active=True)
        except Cart.DoesNotExist:
            cart = Cart.objects.create()
            request.session['cart_id'] = cart.id
            return cart
    else:
        cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
        return cart

@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_or_create_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(request, f'✓ {product.name} agregado al carrito')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart.get_item_count(),
            'cart_total': float(cart.get_total())
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'menu'))

def view_cart(request):
    cart = get_or_create_cart(request)
    return render(request, 'cart/cart.html', {'cart': cart})

@require_POST
def update_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    quantity = int(request.POST.get('quantity', 0))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    return redirect('cart:cart')

@require_POST
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('cart:cart')