from .models import Cart

def cart(request):
    cart_id = request.session.get('cart_id')
    cart = None
    
    if cart_id:
        try:
            cart = Cart.objects.get(id=cart_id, is_active=True)
        except Cart.DoesNotExist:
            pass
    
    return {
        'cart_count': cart.get_item_count() if cart else 0,
        'cart_total': cart.get_total() if cart else 0,
        'cart': cart
    }