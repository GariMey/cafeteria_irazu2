# D:\cafeteria_irazu_proyecto\cafeteria_irazu\bookings\models.py
from django.db import models

class Table(models.Model):
    number = models.IntegerField(unique=True, verbose_name="Número de Mesa")
    capacity = models.IntegerField(default=4, verbose_name="Capacidad")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    
    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['number']
    
    def __str__(self):
        return f"Mesa {self.number} ({self.capacity} pers.)"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Completada'),
        ('cancelled', 'Cancelada'),
    ]
    
    customer_name = models.CharField(max_length=100, verbose_name="Nombre")
    customer_email = models.EmailField(verbose_name="Email")
    customer_phone = models.CharField(max_length=20, verbose_name="Teléfono")
    date = models.DateField(verbose_name="Fecha")
    time = models.TimeField(verbose_name="Hora")
    guests = models.IntegerField(default=2, verbose_name="Personas")
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Mesa")
    special_requests = models.TextField(blank=True, verbose_name="Solicitudes especiales")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creada")
    
    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.customer_name} - {self.date} {self.time}"