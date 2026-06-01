import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafeteria_irazu.settings')
django.setup()

from dashboard.models import Pedido

productos = [
    ('Café con leche', 800),
    ('Gallo pinto', 1500),
    ('Casado corriente', 2500),
    ('Empanada de queso', 600),
    ('Natilla con miel', 700),
    ('Refresco natural', 500),
    ('Arroz con leche', 900),
    ('Tamal', 1200),
    ('Pan de yuca', 400),
    ('Chocolate caliente', 750),
]

clientes = [
    'María González', 'Carlos Pérez', 'Ana Jiménez',
    'Luis Rodríguez', 'Laura Mora', 'José Vargas',
    'Sofía Castro', 'Diego Solís', 'Andrea Quesada',
    'Andrés Rojas',
]

estados = ['completado', 'completado', 'completado', 'pendiente']

print("Insertando datos...")
Pedido.objects.all().delete()

for i in range(200):
    producto, precio = random.choice(productos)
    cantidad = random.randint(1, 5)
    estado = random.choice(estados)
    dias = random.randint(0, 90)
    hora = random.choice([7, 8, 8, 9, 10, 12, 12, 13, 14, 15, 16])
    fecha = datetime.now() - timedelta(days=dias)
    fecha = fecha.replace(hour=hora, minute=random.randint(0, 59))

    Pedido.objects.create(
        cliente=random.choice(clientes),
        producto=producto,
        cantidad=cantidad,
        total=precio * cantidad,
        estado=estado,
        fecha_hora=fecha,
    )

print(f"✅ Se insertaron {Pedido.objects.count()} pedidos correctamente.")