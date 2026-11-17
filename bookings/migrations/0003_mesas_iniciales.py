from django.db import migrations

# Mesas de la cafetería: 10 de 4 personas y 4 de 6 personas
TABLES = [(n, 4) for n in range(1, 11)] + [(n, 6) for n in range(11, 15)]


def create_tables(apps, schema_editor):
    Table = apps.get_model('bookings', 'Table')
    if Table.objects.exists():
        return   # ya hay mesas configuradas: no se tocan
    Table.objects.bulk_create([Table(number=n, capacity=c) for n, c in TABLES])


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0002_alter_table_options_alter_reservation_created_at_and_more'),
    ]

    operations = [
        migrations.RunPython(create_tables, migrations.RunPython.noop),
    ]
