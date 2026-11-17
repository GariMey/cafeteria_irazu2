from django.db import migrations, models
from django.utils import timezone


def mark_existing_orders(apps, schema_editor):
    """Los pedidos anteriores al panel no deben aparecer como "Nuevos"."""
    Payment = apps.get_model('payments', 'Payment')
    Payment.objects.filter(status='completed').update(order_status='delivered')
    Payment.objects.filter(status__in=['failed', 'refunded']).update(order_status='cancelled')
    # Por privacidad, los pedidos ya cerrados no conservan datos de contacto
    Payment.objects.exclude(order_status='new').update(contact_name='', contact_email='')


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0004_factura'),
    ]

    operations = [
        migrations.RenameField('payment', 'pending_customer_name', 'contact_name'),
        migrations.RenameField('payment', 'pending_customer_email', 'contact_email'),
        migrations.AlterField(
            model_name='payment', name='contact_name',
            field=models.CharField(blank=True, max_length=100, verbose_name='Nombre'),
        ),
        migrations.AlterField(
            model_name='payment', name='contact_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Correo'),
        ),
        migrations.AddField(
            model_name='payment', name='contact_phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='Teléfono'),
        ),
        migrations.AddField(
            model_name='payment', name='delivery_address',
            field=models.CharField(blank=True, max_length=300, verbose_name='Dirección'),
        ),
        migrations.AddField(
            model_name='payment', name='delivery_notes',
            field=models.CharField(blank=True, max_length=200, verbose_name='Indicaciones'),
        ),
        migrations.AddField(
            model_name='payment', name='order_status',
            field=models.CharField(choices=[('new', 'Nuevo'), ('preparing', 'Preparando'),
                                            ('ready', 'Listo para recoger'), ('on_the_way', 'En camino'),
                                            ('delivered', 'Entregado'), ('cancelled', 'Cancelado')],
                                   default='new', max_length=20, verbose_name='Estado del pedido'),
        ),
        migrations.AddField(
            model_name='payment', name='updated_at',
            field=models.DateTimeField(auto_now=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='payment', name='status',
            field=models.CharField(choices=[('pending', 'Pendiente'), ('completed', 'Completado'),
                                            ('failed', 'Fallido'), ('refunded', 'Reembolsado')],
                                   default='pending', max_length=20, verbose_name='Estado del pago'),
        ),
        migrations.RunPython(mark_existing_orders, migrations.RunPython.noop),
    ]
