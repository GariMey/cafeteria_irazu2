# D:\cafeteria_irazu_proyecto\cafeteria_irazu\bookings\admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Table, Reservation

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['number', 'capacity', 'is_active']
    list_editable = ['capacity', 'is_active']
    list_filter = ['is_active']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'date', 'time', 'guests', 'table', 'status', 'created_at']
    list_filter = ['status', 'date', 'table']
    list_editable = ['status', 'table']
    search_fields = ['customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Detalles de la Reserva', {
            'fields': ('date', 'time', 'guests', 'table', 'special_requests')
        }),
        ('Estado', {
            'fields': ('status', 'created_at')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('table')