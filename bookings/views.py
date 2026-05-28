# D:\cafeteria_irazu_proyecto\cafeteria_irazu\bookings\views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ReservationForm

def create_booking(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            
            # Enviar email al cliente
            try:
                send_mail(
                    subject='✅ Reserva Confirmada - Cafetería Irazú',
                    message=f"""
Hola {reservation.customer_name},

¡Gracias por reservar en Cafetería Irazú!

📅 Fecha: {reservation.date}
⏰ Hora: {reservation.time}
👥 Personas: {reservation.guests}

📍 Dirección: Ruta 219, Cot, Cartago

📞 Si necesitas modificar o cancelar, llámanos al 6353-1551

¡Te esperamos!
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[reservation.customer_email],
                    fail_silently=True,
                )
            except:
                pass
            
            # Opcional: También enviar notificación al dueño
            try:
                send_mail(
                    subject='📅 Nueva Reserva - Cafetería Irazú',
                    message=f"""
Nueva reserva creada:

Cliente: {reservation.customer_name}
Email: {reservation.customer_email}
Teléfono: {reservation.customer_phone}
Fecha: {reservation.date}
Hora: {reservation.time}
Personas: {reservation.guests}

Revisa el panel de admin para más detalles.
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=['melanygarita0@gmail.com'],  # email como dueño
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, f'✅ Reserva creada para el {reservation.date} a las {reservation.time}. ¡Te esperamos!')
            return redirect('bookings:booking_success')
    else:
        form = ReservationForm()
    
    return render(request, 'bookings/create_booking.html', {'form': form})

def booking_success(request):
    return render(request, 'bookings/success.html')