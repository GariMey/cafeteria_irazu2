from django.db import models
from cafeteria.models import Product
from cart.models import Cart

class Payment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]
    
    PAYMENT_METHOD = [
        ('card', 'Tarjeta de Crédito/Débito'),
        ('sinpe', 'Sinpe Móvil'),
        ('cash', 'Efectivo en tienda'),
    ]
    
    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='card')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - ₡{self.amount} - {self.status}"

class PaymentItem(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def get_subtotal(self):
        return self.price * self.quantity
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name}"