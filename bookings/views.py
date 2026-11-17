import threading

from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ReservationForm
from .notifications import send_new_to_cafe, send_received


def _notify(reservation):
    # Errores ya se registran en el log dentro de try_send_branded
    send_received(reservation)
    send_new_to_cafe(reservation)


def create_booking(request):
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save()
            # Los correos salen en segundo plano para que la página responda rápido.
            # La reserva queda pendiente hasta que la cafetería la confirme en el panel.
            threading.Thread(target=_notify, args=(reservation,), daemon=True).start()
            messages.success(request, f'Recibimos tu reserva para el {reservation.date} a las '
                                      f'{reservation.time}. Te confirmaremos por correo.')
            return redirect('bookings:booking_success')
    else:
        form = ReservationForm()

    return render(request, 'bookings/create_booking.html', {'form': form})


def booking_success(request):
    return render(request, 'bookings/success.html')
