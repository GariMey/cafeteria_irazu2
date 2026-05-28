# D:\cafeteria_irazu_proyecto\cafeteria_irazu\bookings\urls.py
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.create_booking, name='create_booking'),
    path('success/', views.booking_success, name='booking_success'),
]