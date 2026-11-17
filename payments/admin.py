from django.contrib import admin, messages
from django.utils.html import format_html
from .invoices import confirm_sinpe, reject_sinpe
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
    list_display = ['transaction_id', 'order_status', 'fulfillment', 'amount_display', 'status_badge', 'payment_method', 'reference', 'invoice_number', 'created_at']
    list_filter = ['order_status', 'status', 'fulfillment', 'payment_method', 'created_at']
    list_editable = []
    search_fields = ['transaction_id', 'reference', 'invoice_number']
    readonly_fields = ['transaction_id', 'created_at', 'fulfillment', 'payment_method', 'reference', 'subtotal', 'tax',
                       'delivery_fee', 'amount_display', 'status_badge', 'invoice_number', 'invoiced_at']
    actions = ['confirm_sinpe_action', 'reject_sinpe_action']
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
        # Los datos personales del cliente no se guardan (ver Payment)
        ('Pedido', {
            'fields': ('transaction_id', 'order_status', 'fulfillment', 'status', 'payment_method', 'reference')
        }),
        ('Montos', {
            'fields': ('subtotal', 'delivery_fee', 'tax', 'amount_display')
        }),
        ('Factura', {
            'fields': ('invoice_number', 'invoiced_at')
        }),
        ('Fechas', {
            'fields': ('created_at',)
        }),
    )

    # ── Confirmación de SINPE ──────────────────────────────────────────────
    def save_model(self, request, obj, form, change):
        """Al cambiar el estado a mano, se envía la factura o el aviso de rechazo."""
        # Pedido cerrado: los datos de contacto del cliente se borran
        if 'order_status' in form.changed_data and obj.order_status in obj.FINAL_ORDER_STATUSES:
            obj.forget_contact()
        super().save_model(request, obj, form, change)
        if not change or 'status' not in form.changed_data or obj.payment_method != 'sinpe':
            return
        if obj.status == 'completed':
            self._report_invoice(request, obj, confirm_sinpe(obj))
        elif obj.status == 'failed':
            reject_sinpe(obj)
            self.message_user(request, f"{obj.transaction_id}: se avisó al cliente que el SINPE fue rechazado.")

    def _report_invoice(self, request, payment, sent):
        if sent:
            self.message_user(request, f"{payment.transaction_id}: factura {payment.invoice_number} enviada al cliente.")
        elif payment.invoiced_at:
            self.message_user(request, f"{payment.transaction_id}: la factura ya se había enviado.", messages.INFO)
        else:
            self.message_user(request, f"{payment.transaction_id}: no se pudo enviar la factura "
                                       "(no hay correo guardado o falló el envío).", messages.WARNING)

    @admin.action(description="✅ Confirmar SINPE y enviar factura")
    def confirm_sinpe_action(self, request, queryset):
        for payment in queryset.filter(payment_method='sinpe', status='pending'):
            self._report_invoice(request, payment, confirm_sinpe(payment))

    @admin.action(description="❌ Rechazar SINPE y avisar al cliente")
    def reject_sinpe_action(self, request, queryset):
        rejected = 0
        for payment in queryset.filter(payment_method='sinpe', status='pending'):
            reject_sinpe(payment)
            rejected += 1
        self.message_user(request, f"{rejected} pago(s) SINPE rechazado(s); se avisó a los clientes.")

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
