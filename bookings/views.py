from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ReservationForm
from .notifications import received_body
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

            # Aviso al cliente en segundo plano: la reserva queda pendiente hasta
            # que la cafetería la confirme desde el panel (/panel/reservas/)
            threading.Thread(target=send_email_async, args=(
                'Recibimos tu reserva - Cafetería Irazú',
                received_body(reservation),
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
Personas: {reservation.guests}

Confírmala o cancélala en el panel: Reservas.""",
                settings.DEFAULT_FROM_EMAIL,
                [settings.CAFE_EMAIL],
            )).start()

            messages.success(request, f'Recibimos tu reserva para el {reservation.date} a las {reservation.time}. Te confirmaremos por correo.')
            return redirect('bookings:booking_success')
    else:
        form = ReservationForm()

    return render(request, 'bookings/create_booking.html', {'form': form})

def booking_success(request):
    return render(request, 'bookings/success.html')
