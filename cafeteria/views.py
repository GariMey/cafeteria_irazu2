# D:\cafeteria_irazu_proyecto\cafeteria_irazu\cafeteria\views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from .models import Category, Product, GalleryImage, Testimonial, ContactMessage
from .forms import ContactForm, TestimonialForm

def home(request):
    categories = Category.objects.prefetch_related('products').filter(products__isnull=False).distinct()
    featured_products = Product.objects.filter(featured=True, available=True).select_related('category')[:8]
    gallery_images = GalleryImage.objects.all()[:9]
    testimonials = Testimonial.objects.filter(active=True)[:6]
    contact_form = ContactForm()
    testimonial_form = TestimonialForm()

    if request.method == 'POST':
        # Procesar testimonio
        if 'submit_testimonial' in request.POST:
            testimonial_form = TestimonialForm(request.POST)
            if testimonial_form.is_valid():
                testimonial = testimonial_form.save(commit=False)
                testimonial.active = True
                testimonial.save()
                messages.success(request, 'Gracias por tu testimonio. Tu opinion ya esta publicada.')
                return redirect('/#dejar-testimonio')
        
        # Procesar contacto -
        if 'submit_contact' in request.POST:
            contact_form = ContactForm(request.POST)
            if contact_form.is_valid():
                contact_message = contact_form.save()
                
                # Enviar email al dueno del cafe
                try:
                    send_mail(
                        subject='Nuevo mensaje de contacto - Cafeteria Irazu',
                        message=f"""
NUEVO MENSAJE DE CONTACTO

DATOS DEL CLIENTE:
   Nombre: {contact_message.name}
   Email: {contact_message.email}
   Telefono: {contact_message.phone or 'No especificado'}

MENSAJE:
{contact_message.message}

Fecha: {contact_message.created_at.strftime('%d/%m/%Y %H:%M')}

Responder a: {contact_message.email}
Llamar a: {contact_message.phone or 'No disponible'}

Cafeteria Irazu - Cartago, Costa Rica
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.CAFE_EMAIL] if hasattr(settings, 'CAFE_EMAIL') else ['melanygaritauu1276@gmail.com'],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Error al enviar email: {e}")
                
                # Enviar email de confirmacion al cliente
                try:
                    send_mail(
                        subject='Hemos recibido tu mensaje - Cafeteria Irazu',
                        message=f"""
Hola {contact_message.name},

Gracias por contactarnos. Hemos recibido tu mensaje y te responderemos a la brevedad.

Tu mensaje fue:
"{contact_message.message}"

Tiempo estimado de respuesta: 24 horas

Te esperamos pronto en Cafeteria Irazu.

Saludos cordiales,
El equipo de Cafeteria Irazu
                        """,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[contact_message.email],
                        fail_silently=True,
                    )
                except Exception as e:
                    print(f"Error al enviar email al cliente: {e}")
                
                messages.success(request, f'Gracias {contact_message.name}. Tu mensaje ha sido enviado. Te contactaremos pronto.')
                return HttpResponseRedirect('/#contacto')
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'gallery_images': gallery_images,
        'testimonials': testimonials,
        'contact_form': contact_form,
        'testimonial_form': testimonial_form,
    }
    return render(request, 'cafeteria/home.html', context)


def menu(request):
    categories = Category.objects.prefetch_related('products').filter(products__available=True).distinct()
    return render(request, 'cafeteria/menu.html', {'categories': categories})