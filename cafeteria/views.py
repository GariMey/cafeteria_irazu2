# D:\cafeteria_irazu_proyecto\cafeteria_irazu\cafeteria\views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Category, Product, GalleryImage, Testimonial
from .forms import ContactForm

def home(request):
    categories = Category.objects.prefetch_related('products').filter(products__isnull=False).distinct()
    featured_products = Product.objects.filter(featured=True, available=True).select_related('category')[:8]
    gallery_images = GalleryImage.objects.all()[:9]
    testimonials = Testimonial.objects.filter(active=True)[:6]
    contact_form = ContactForm()

    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, '¡Mensaje enviado con éxito! Te contactaremos pronto. ☕')
            return redirect('home#contacto')

    context = {
        'categories': categories,
        'featured_products': featured_products,
        'gallery_images': gallery_images,
        'testimonials': testimonials,
        'contact_form': contact_form,
    }
    return render(request, 'cafeteria/home.html', context)


def menu(request):
    # Obtener todas las categorías con sus productos disponibles
    categories = Category.objects.prefetch_related('products').filter(products__available=True).distinct()
    return render(request, 'cafeteria/menu.html', {'categories': categories})