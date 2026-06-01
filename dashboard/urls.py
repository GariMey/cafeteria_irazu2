from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('reto1/', views.reto1, name='reto1'),
    path('reto2/', views.reto2, name='reto2'),
    path('reto3/', views.reto3, name='reto3'),
]