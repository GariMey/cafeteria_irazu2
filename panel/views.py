"""Panel del negocio: pedidos, productos y mensajes de contacto.

Solo pueden entrar usuarios con is_staff (personal de la cafetería).
"""
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cafeteria.models import Category, ContactMessage, ExperienceFeature, GalleryImage, Product
from payments.invoices import confirm_sinpe, reject_sinpe
from payments.models import Payment
from payments.orders import OrderError, advance_order, cancel_order, purge_stale_contacts

from .forms import (ExperienceFeatureForm, GalleryImageForm, GalleryUploadForm, ProductForm,
                    ReplyForm)

logger = logging.getLogger(__name__)


# Exige un usuario del personal; si no, manda al login del panel
staff_required = user_passes_test(lambda u: u.is_active and u.is_staff, login_url='panel:login')


def _counters():
    """Números de los avisos del menú del panel."""
    return {
        'new_orders': Payment.objects.filter(order_status=Payment.NEW).count(),
        'pending_sinpe': Payment.objects.filter(payment_method='sinpe', status='pending',
                                                order_status__in=Payment.ACTIVE_ORDER_STATUSES).count(),
        'unread_messages': ContactMessage.objects.filter(read=False).count(),
    }


def _render(request, template, context=None, section=''):
    return render(request, template, {**(context or {}), 'counters': _counters(), 'section': section})


@staff_required
def home(request):
    return redirect('panel:orders')


# ── Pedidos ────────────────────────────────────────────────────────────────
@staff_required
def orders(request):
    purge_stale_contacts()
    active = (Payment.objects.filter(order_status__in=Payment.ACTIVE_ORDER_STATUSES)
              .prefetch_related('items').order_by('created_at'))
    context = {
        'active_orders': active,
        'closed_orders': (Payment.objects.filter(order_status__in=Payment.FINAL_ORDER_STATUSES)
                          .prefetch_related('items').order_by('-updated_at')[:20]),
        'newest_id': active.order_by('-id').values_list('id', flat=True).first() or 0,
    }
    # El JavaScript del panel pide solo la lista para actualizarla sin recargar
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return _render(request, 'panel/_orders_list.html', context, 'orders')
    return _render(request, 'panel/orders.html', context, 'orders')


@staff_required
@require_POST
def order_action(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    action = request.POST.get('action')
    try:
        if action == 'advance':
            advance_order(payment, request.POST.get('to'))
            messages.success(request, f"{payment.transaction_id}: {payment.get_order_status_display()}.")
        elif action == 'cancel':
            cancel_order(payment)
            messages.success(request, f"{payment.transaction_id}: pedido cancelado.")
        elif action == 'confirm_sinpe' and payment.awaiting_sinpe:
            if confirm_sinpe(payment):
                messages.success(request, f"SINPE confirmado. Factura {payment.invoice_number} enviada al cliente.")
            else:
                messages.warning(request, "SINPE confirmado, pero no se pudo enviar la factura.")
        elif action == 'reject_sinpe' and payment.awaiting_sinpe:
            reject_sinpe(payment)
            messages.success(request, "SINPE rechazado. Se avisó al cliente y el pedido quedó cancelado.")
        else:
            messages.error(request, "Acción no válida.")
    except OrderError as error:
        messages.error(request, str(error))
    return redirect('panel:orders')


# ── Productos ──────────────────────────────────────────────────────────────
@staff_required
def products(request):
    qs = Product.objects.select_related('category').order_by('category__name', 'name')
    query = request.GET.get('q', '').strip()
    category = request.GET.get('categoria', '')
    if query:
        qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category.isdigit():
        qs = qs.filter(category_id=int(category))
    return _render(request, 'panel/products.html', {
        'products': qs, 'categories': Category.objects.order_by('name'),
        'query': query, 'selected_category': category,
    }, 'products')


@staff_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        messages.success(request, f"Producto «{saved.name}» {'actualizado' if product else 'creado'}.")
        return redirect('panel:products')
    return _render(request, 'panel/product_form.html', {'form': form, 'product': product}, 'products')


@staff_required
@require_POST
def product_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    field = request.POST.get('field')
    if field not in ('available', 'featured'):
        messages.error(request, "Acción no válida.")
    else:
        setattr(product, field, not getattr(product, field))
        product.save(update_fields=[field])
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = 'panel:products'
    return redirect(next_url)


@staff_required
@require_POST
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    name = product.name
    product.delete()
    messages.success(request, f"Producto «{name}» eliminado.")
    return redirect('panel:products')


# ── Galería ────────────────────────────────────────────────────────────────
HOME_GALLERY_LIMIT = 9   # la página de inicio muestra las primeras 9 (ver cafeteria.views.home)


def _delete_file(field):
    """Borra el archivo del almacenamiento (Cloudinary o media/) sin romper si falla."""
    if field:
        try:
            field.delete(save=False)
        except Exception:
            logger.exception("No se pudo borrar el archivo %s", field.name)


@staff_required
def gallery(request):
    form = GalleryUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        next_order = (GalleryImage.objects.order_by('-order').values_list('order', flat=True).first() or 0) + 1
        images = form.cleaned_data['images']
        for i, upload in enumerate(images):
            GalleryImage.objects.create(image=upload, order=next_order + i)
        messages.success(request, f"{len(images)} foto{'s' if len(images) != 1 else ''} agregada{'s' if len(images) != 1 else ''} a la galería.")
        return redirect('panel:gallery')
    return _render(request, 'panel/gallery.html', {
        'form': form,
        'images': [(img, GalleryImageForm(instance=img, prefix=f'img{img.pk}'))
                   for img in GalleryImage.objects.all()],
        'home_limit': HOME_GALLERY_LIMIT,
    }, 'gallery')


@staff_required
@require_POST
def gallery_update(request, pk):
    image = get_object_or_404(GalleryImage, pk=pk)
    form = GalleryImageForm(request.POST, instance=image, prefix=f'img{pk}')
    if form.is_valid():
        form.save()
        messages.success(request, "Foto actualizada.")
    else:
        messages.error(request, "Revisa el título y el orden.")
    return redirect('panel:gallery')


@staff_required
@require_POST
def gallery_delete(request, pk):
    image = get_object_or_404(GalleryImage, pk=pk)
    _delete_file(image.image)
    image.delete()
    messages.success(request, "Foto eliminada de la galería.")
    return redirect('panel:gallery')


# ── La Experiencia Irazú ───────────────────────────────────────────────────
@staff_required
def experience(request):
    return _render(request, 'panel/experience.html',
                   {'features': ExperienceFeature.objects.all()}, 'experience')


@staff_required
def experience_form(request, pk=None):
    feature = get_object_or_404(ExperienceFeature, pk=pk) if pk else None
    old_image = feature.image.name if feature and feature.image else ''
    form = ExperienceFeatureForm(request.POST or None, request.FILES or None, instance=feature)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        # Si se reemplazó o quitó la imagen subida, se borra la anterior
        if old_image and saved.image.name != old_image:
            try:
                saved.image.storage.delete(old_image)
            except Exception:
                logger.exception("No se pudo borrar la imagen anterior %s", old_image)
        messages.success(request, f"Tarjeta «{saved.title}» {'actualizada' if feature else 'creada'}.")
        return redirect('panel:experience')
    return _render(request, 'panel/experience_form.html', {'form': form, 'feature': feature}, 'experience')


@staff_required
@require_POST
def experience_delete(request, pk):
    feature = get_object_or_404(ExperienceFeature, pk=pk)
    _delete_file(feature.image)
    title = feature.title
    feature.delete()
    messages.success(request, f"Tarjeta «{title}» eliminada.")
    return redirect('panel:experience')


# ── Mensajes ───────────────────────────────────────────────────────────────
@staff_required
def inbox(request):
    show = request.GET.get('ver', 'todos')
    qs = ContactMessage.objects.order_by('read', '-created_at')
    if show == 'sin-leer':
        qs = qs.filter(read=False)
    elif show == 'sin-responder':
        qs = qs.filter(replied_at__isnull=True)
    return _render(request, 'panel/inbox.html', {'contact_messages': qs, 'show': show}, 'inbox')


@staff_required
def message_detail(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    if not message.read:
        message.read = True
        message.save(update_fields=['read'])

    form = ReplyForm(request.POST or None, initial={
        'subject': 'Re: Tu mensaje a Cafetería Irazú',
        'body': f"Hola {message.name},\n\n\n\nSaludos,\nCafetería Irazú",
    })
    if request.method == 'POST' and form.is_valid():
        body = form.cleaned_data['body']
        quoted = "\n".join(f"> {line}" for line in message.message.splitlines())
        email = EmailMessage(
            subject=form.cleaned_data['subject'],
            body=(f"{body}\n\n"
                  f"--- Tu mensaje del {timezone.localtime(message.created_at):%d/%m/%Y %H:%M} ---\n{quoted}"),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[message.email],
            # Si el cliente contesta, la respuesta llega al correo de la cafetería
            reply_to=[settings.CAFE_EMAIL],
        )
        try:
            email.send()
        except Exception:
            logger.exception("No se pudo enviar la respuesta al mensaje %s", message.pk)
            messages.error(request, "No se pudo enviar el correo. Revisa la configuración de Gmail.")
        else:
            message.reply = body
            message.replied_at = timezone.now()
            message.save(update_fields=['reply', 'replied_at'])
            messages.success(request, f"Respuesta enviada a {message.email}.")
            return redirect('panel:message', pk=message.pk)
    return _render(request, 'panel/message.html', {'message': message, 'form': form}, 'inbox')


@staff_required
@require_POST
def message_action(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    action = request.POST.get('action')
    if action == 'unread':
        message.read = False
        message.save(update_fields=['read'])
        messages.success(request, "Marcado como no leído.")
    elif action == 'delete':
        message.delete()
        messages.success(request, "Mensaje eliminado.")
    return redirect('panel:inbox')
