from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, PaymentItem

class PaymentItemInline(admin.TabularInline):
    model = PaymentItem
    extra = 0
    readonly_fields = ['product_name', 'quantity', 'price', 'get_subtotal_display']
    
    def get_subtotal_display(self, obj):
        return f"₡{obj.get_subtotal():,.0f}"
    get_subtotal_display.short_description = "Subtotal"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'customer_name', 'amount_display', 'status_badge', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    list_editable = []
    search_fields = ['transaction_id', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['transaction_id', 'created_at', 'amount_display', 'status_badge']
    inlines = [PaymentItemInline]
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        return f"₡{obj.amount:,.0f}"
    amount_display.short_description = "Monto"
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ff9800',
            'completed': '#4caf50',
            'failed': '#f44336',
            'refunded': '#9e9e9e',
        }
        color = colors.get(obj.status, '#9e9e9e')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = "Estado"
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Información del Pago', {
            'fields': ('transaction_id', 'amount_display', 'status', 'payment_method')
        }),
        ('Fechas', {
            'fields': ('created_at',)
        }),
    )

@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = ['payment_link', 'product_name', 'quantity', 'price_display', 'subtotal_display']
    list_filter = ['payment__status']
    search_fields = ['product_name', 'payment__transaction_id']
    
    def payment_link(self, obj):
        return format_html('<a href="/admin/payments/payment/{}/change/">#{}</a>', obj.payment.id, obj.payment.transaction_id)
    payment_link.short_description = "Pago"
    
    def price_display(self, obj):
        return f"₡{obj.price:,.0f}"
    price_display.short_description = "Precio"
    
    def subtotal_display(self, obj):
        return f"₡{obj.get_subtotal():,.0f}"
    subtotal_display.short_description = "Subtotal"
