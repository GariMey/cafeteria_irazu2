# D:\cafeteria_irazu_proyecto\cafeteria_irazu\cafeteria\admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, GalleryImage, Testimonial, ContactMessage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'icon']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'featured', 'available']
    list_filter = ['category', 'featured', 'available']
    list_editable = ['featured', 'available']
    search_fields = ['name']

@admin.register(GalleryImage)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    list_editable = ['order']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating_stars', 'comment_preview', 'active', 'created_at']
    list_filter = ['rating', 'active', 'created_at']
    list_editable = ['active']
    search_fields = ['name', 'comment']
    list_per_page = 20
    
    def rating_stars(self, obj):
        """Muestra estrellas en lugar del número"""
        return '⭐' * obj.rating
    rating_stars.short_description = "Calificación"
    
    def comment_preview(self, obj):
        """Muestra un preview del comentario"""
        if len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment
    comment_preview.short_description = "Comentario"
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('name', 'rating', 'active')
        }),
        ('Testimonio', {
            'fields': ('comment',),
            'description': 'El comentario que aparecerá en la página principal'
        }),
        ('Fechas', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['created_at']

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'read', 'created_at']
    list_editable = ['read']
    list_filter = ['read']
    readonly_fields = ['name', 'email', 'phone', 'message', 'created_at']

