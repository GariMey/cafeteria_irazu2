from django.db import models

class Pedido(models.Model):
    ESTADO_CHOICES = [
        ('completado', 'Completado'),
        ('pendiente', 'Pendiente'),
    ]
    
    cliente = models.CharField(max_length=100)
    producto = models.CharField(max_length=100)
    cantidad = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_hora = models.DateTimeField()

    def __str__(self):
        return f"{self.cliente} - {self.producto}"

    class Meta:
        ordering = ['-fecha_hora']