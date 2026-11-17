import uuid

from django.db import models

from cart.models import Cart

from .pricing import FULFILLMENT_CHOICES, PICKUP


class Payment(models.Model):
    """Registro de un pedido pagado.

    Por privacidad NO guarda datos personales del cliente (teléfono,
    dirección) ni datos de la tarjeta: esos datos solo se usan para validar
    el pago y enviar los correos, y luego se descartan. La única excepción
    es el nombre y correo de un pago SINPE pendiente, que se guardan hasta
    enviar la factura y después se borran.
    """
    PAYMENT_STATUS = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    ]

    PAYMENT_METHOD = [
        ('card', 'Tarjeta de Crédito/Débito'),
        ('sinpe', 'SINPE Móvil'),
        ('google_pay', 'Google Pay'),
        ('apple_pay', 'Apple Pay'),
        ('cash', 'Efectivo en tienda'),
    ]

    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    fulfillment = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default=PICKUP,
                                   verbose_name="Tipo de entrega")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Envío")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='card')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    # Comprobante SINPE para que la cafetería verifique el depósito (no es dato personal)
    reference = models.CharField(max_length=40, blank=True, verbose_name="Comprobante SINPE")

    # Factura enviada al cliente cuando el pago queda confirmado
    invoice_number = models.CharField(max_length=20, blank=True, verbose_name="N.º de factura")
    invoiced_at = models.DateTimeField(null=True, blank=True, verbose_name="Factura enviada")

    # Contacto TEMPORAL: solo para pagos SINPE pendientes, porque la factura se
    # envía después, cuando la cafetería confirma el depósito. Se borra en
    # cuanto se envía la factura o se rechaza el pago (ver payments.invoices).
    pending_customer_name = models.CharField(max_length=100, blank=True)
    pending_customer_email = models.EmailField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.transaction_id:
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
