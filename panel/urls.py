from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import StaffLoginForm

app_name = 'panel'

urlpatterns = [
    path('', views.home, name='home'),
    path('entrar/', auth_views.LoginView.as_view(
        template_name='panel/login.html', authentication_form=StaffLoginForm,
        next_page=reverse_lazy('panel:orders')), name='login'),
    path('salir/', auth_views.LogoutView.as_view(next_page=reverse_lazy('panel:login')), name='logout'),

    path('pedidos/', views.orders, name='orders'),
    path('pedidos/<int:pk>/accion/', views.order_action, name='order_action'),

    path('productos/', views.products, name='products'),
    path('productos/nuevo/', views.product_form, name='product_new'),
    path('productos/<int:pk>/', views.product_form, name='product_edit'),
    path('productos/<int:pk>/cambiar/', views.product_toggle, name='product_toggle'),
    path('productos/<int:pk>/eliminar/', views.product_delete, name='product_delete'),

    path('galeria/', views.gallery, name='gallery'),
    path('galeria/<int:pk>/', views.gallery_update, name='gallery_update'),
    path('galeria/<int:pk>/eliminar/', views.gallery_delete, name='gallery_delete'),

    path('experiencia/', views.experience, name='experience'),
    path('experiencia/nueva/', views.experience_form, name='experience_new'),
    path('experiencia/<int:pk>/', views.experience_form, name='experience_edit'),
    path('experiencia/<int:pk>/eliminar/', views.experience_delete, name='experience_delete'),

    path('mensajes/', views.inbox, name='inbox'),
    path('mensajes/<int:pk>/', views.message_detail, name='message'),
    path('mensajes/<int:pk>/accion/', views.message_action, name='message_action'),
]
