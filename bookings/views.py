from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ReservationForm
import threading

def send_email_async(subject, message, from_email, recipient_list):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True,
        )
    except:
        pass

def create_booking(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()

            # Enviar email al cliente en segundo plano
            threading.Thread(target=send_email_async, args=(
                'Reserva Confirmada - Cafetería Irazú',
                f"""Hola {reservation.customer_name},

¡Gracias por reservar en Cafetería Irazú!

Fecha: {reservation.date}
Hora: {reservation.time}
Personas: {reservation.guests}

Dirección: Cartago

Si necesitas modificar o cancelar, llámanos al 6353-1551

¡Te esperamos!""",
                settings.DEFAULT_FROM_EMAIL,
                [reservation.customer_email],
            )).start()

            # Notificación al dueño en segundo plano
            threading.Thread(target=send_email_async, args=(
                'Nueva Reserva - Cafetería Irazú',
                f"""Nueva reserva creada:

Cliente: {reservation.customer_name}
Email: {reservation.customer_email}
Teléfono: {reservation.customer_phone}
Fecha: {reservation.date}
Hora: {reservation.time}
Personas: {reservation.guests}""",
                settings.DEFAULT_FROM_EMAIL,
                ['cuaderno.melanygr@gmail.com'],
            )).start()

            messages.success(request, f'Reserva creada para el {reservation.date} a las {reservation.time}. ¡Te esperamos!')
            return redirect('bookings:booking_success')
    else:
        form = ReservationForm()

    return render(request, 'bookings/create_booking.html', {'form': form})

def booking_success(request):
    return render(request, 'bookings/success.html')
