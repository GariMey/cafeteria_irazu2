# D:\cafeteria_irazu_proyecto\cafeteria_irazu\cafeteria\views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseRedirect
from .models import Category, Product, GalleryImage, Testimonial, ContactMessage, ExperienceFeature
from .emails import try_send_branded
from .forms import ContactForm, TestimonialForm

def home(request):
    categories = Category.objects.prefetch_related('products').filter(products__isnull=False).distinct()
    featured_products = Product.objects.filter(featured=True, available=True).select_related('category')[:8]
    gallery_images = GalleryImage.objects.all()[:9]
    experience_features = ExperienceFeature.objects.filter(active=True)
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
                
                # Aviso a la cafetería (responder le escribe al cliente) y acuse al cliente
                fecha = timezone.localtime(contact_message.created_at).strftime('%d/%m/%Y %H:%M')
                try_send_branded(
                    f'Nuevo mensaje de {contact_message.name} - Cafetería Irazú', 'contact_new_cafe',
                    {'msg': contact_message,
                     'rows': [('Nombre', contact_message.name), ('Correo', contact_message.email),
                              ('Teléfono', contact_message.phone or 'No indicado'), ('Fecha', fecha)]},
                    [settings.CAFE_EMAIL], reply_to=[contact_message.email],
                )
                try_send_branded(
                    'Recibimos tu mensaje - Cafetería Irazú', 'contact_received',
                    {'msg': contact_message}, [contact_message.email],
                )

                messages.success(request, f'Gracias {contact_message.name}. Tu mensaje ha sido enviado. Te contactaremos pronto.')
                return HttpResponseRedirect('/#contacto')
    
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'gallery_images': gallery_images,
        'experience_features': experience_features,
        'testimonials': testimonials,
        'contact_form': contact_form,
        'testimonial_form': testimonial_form,
    }
    return render(request, 'cafeteria/home.html', context)


def menu(request):
    categories = Category.objects.prefetch_related('products').filter(products__available=True).distinct()
    return render(request, 'cafeteria/menu.html', {'categories': categories})