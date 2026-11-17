from django.core.management import call_command
from django.core.management.base import BaseCommand

from cafeteria.models import Category, Product


class Command(BaseCommand):
    help = "Carga el menú inicial (cafeteria/fixtures/menu.json) solo si todavía no hay productos."

    def handle(self, *args, **options):
        if Product.objects.exists() or Category.objects.exists():
            self.stdout.write("El menú ya tiene datos; no se carga nada.")
            return
        call_command('loaddata', 'menu', verbosity=0)
        self.stdout.write(self.style.SUCCESS(
            f"Menú inicial cargado: {Category.objects.count()} categorías y {Product.objects.count()} productos."))
