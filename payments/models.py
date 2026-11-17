import uuid

from django.db import models

from cart.models import Cart

from .pricing import DELIVERY, FULFILLMENT_CHOICES, PICKUP


class Payment(models.Model):
    """Un pedido pagado (o con pago SINPE pendiente).

    Privacidad:
    - Nunca se guardan datos de la tarjeta ni de la billetera.
    - Los datos de contacto (nombre, correo, teléfono, dirección) se guardan
      solo mientras el pedido está activo, para poder prepararlo, entregarlo
      y enviar la factura. Se borran al marcarlo Entregado o Cancelado, y
      como respaldo a los ORDER_CONTACT_RETENTION_DAYS días (forget_contact).
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

    # Estado de preparación del pedido (distinto del estado del pago)
    NEW, PREPARING, READY, ON_THE_WAY, DELIVERED, CANCELLED = (
        'new', 'preparing', 'ready', 'on_the_way', 'delivered', 'cancelled')
    ORDER_STATUS = [
        (NEW, 'Nuevo'),
        (PREPARING, 'Preparando'),
        (READY, 'Listo para recoger'),
        (ON_THE_WAY, 'En camino'),
        (DELIVERED, 'Entregado'),
        (CANCELLED, 'Cancelado'),
    ]
    ACTIVE_ORDER_STATUSES = (NEW, PREPARING, READY, ON_THE_WAY)
    FINAL_ORDER_STATUSES = (DELIVERED, CANCELLED)

    cart = models.ForeignKey(Cart, on_delete=models.SET_NULL, null=True)
    fulfillment = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default=PICKUP,
                                   verbose_name="Tipo de entrega")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="IVA")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Envío")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending',
                              verbose_name="Estado del pago")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD, default='card')
    transaction_id = models.CharField(max_length=100, unique=True, blank=True)
    # Comprobante SINPE para que la cafetería verifique el depósito (no es dato personal)
    reference = models.CharField(max_length=40, blank=True, verbose_name="Comprobante SINPE")
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS, default=NEW,
                                    verbose_name="Estado del pedido")

    # Factura enviada al cliente cuando el pago queda confirmado
    invoice_number = models.CharField(max_length=20, blank=True, verbose_name="N.º de factura")
    invoiced_at = models.DateTimeField(null=True, blank=True, verbose_name="Factura enviada")

    # Contacto TEMPORAL: solo mientras el pedido está activo (ver docstring)
    contact_name = models.CharField(max_length=100, blank=True, verbose_name="Nombre")
    contact_email = models.EmailField(blank=True, verbose_name="Correo")
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    delivery_address = models.CharField(max_length=300, blank=True, verbose_name="Dirección")
    delivery_notes = models.CharField(max_length=200, blank=True, verbose_name="Indicaciones")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    CONTACT_FIELDS = ('contact_name', 'contact_email', 'contact_phone',
                      'delivery_address', 'delivery_notes')

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

    # ── Ayudas para el panel ───────────────────────────────────────────────
    @property
    def is_delivery(self):
        return self.fulfillment == DELIVERY

    @property
    def is_active_order(self):
        return self.order_status in self.ACTIVE_ORDER_STATUSES

    @property
    def awaiting_sinpe(self):
        return self.payment_method == 'sinpe' and self.status == 'pending'

    @property
    def has_contact(self):
        return any(getattr(self, f) for f in self.CONTACT_FIELDS)

    def next_order_statuses(self):
        """Siguientes estados posibles. Un SINPE sin verificar no avanza."""
        if self.awaiting_sinpe or not self.is_active_order:
            return []
        flow = {
            self.NEW: [self.PREPARING],
            self.PREPARING: [self.ON_THE_WAY if self.is_delivery else self.READY],
            self.READY: [self.DELIVERED],
            self.ON_THE_WAY: [self.DELIVERED],
        }
        return flow.get(self.order_status, [])

    def forget_contact(self):
        """Borra los datos de contacto (no guarda; llamar a save después)."""
        for field in self.CONTACT_FIELDS:
            setattr(self, field, '')


class PaymentItem(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"
