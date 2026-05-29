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
