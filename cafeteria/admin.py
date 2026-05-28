from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Sum, Count
from .models import Category, Product, GalleryImage, Testimonial, ContactMessage
from payments.models import Payment

class CustomAdminSite(AdminSite):
    site_header = "☕ Cafetería Irazú — Administración"
    site_title = "Cafetería Irazú"
    index_title = "Panel de Control"
    
    def index(self, request, extra_context=None):
        # Estadísticas
        total_ventas = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        total_pedidos = Payment.objects.filter(status='completed').count()
        total_productos = Product.objects.count()
        total_mensajes = ContactMessage.objects.filter(read=False).count()
        
        extra_context = {
            'total_ventas': f"₡{total_ventas:,.0f}",
            'total_pedidos': total_pedidos,
            'total_productos': total_productos,
            'total_mensajes': total_mensajes,
        }
        return super().index(request, extra_context)

admin_site = CustomAdminSite(name='custom_admin')