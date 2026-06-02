# D:\cafeteria_irazu_proyecto\cafeteria_irazu\cart\models.py
from django.db import models
from decimal import Decimal

class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"
    
    def get_total(self):
        """Calcula el total del carrito"""
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.get_subtotal()
        return total
    
    def get_item_count(self):
        """Retorna el número total de items"""
        return self.items.count()
    
    def __str__(self):
        return f"Carrito #{self.id}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('cafeteria.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    class Meta:
        unique_together = ['cart', 'product']
        verbose_name = "Item del Carrito"
        verbose_name_plural = "Items del Carrito"
    
    def get_subtotal(self):
        """Calcula subtotal del item"""
        return self.product.price * Decimal(str(self.quantity))
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"