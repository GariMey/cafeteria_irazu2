from django.shortcuts import render
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour
from .models import Pedido
from datetime import datetime

def dashboard(request):
    total_pedidos = Pedido.objects.count()
    total_ingresos = Pedido.objects.aggregate(Sum('total'))['total__sum'] or 0
    total_completados = Pedido.objects.filter(estado='completado').count()
    total_pendientes = Pedido.objects.filter(estado='pendiente').count()

    return render(request, 'dashboard/dashboard.html', {
        'total_pedidos': total_pedidos,
        'total_ingresos': total_ingresos,
        'total_completados': total_completados,
        'total_pendientes': total_pendientes,
    })

def reto1(request):
    pedidos = Pedido.objects.all()
    total = 0
    count = 0
    promedio = 0
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    estado = request.GET.get('estado', '')

    if fecha_desde:
        pedidos = pedidos.filter(fecha_hora__date__gte=fecha_desde)
    if fecha_hasta:
        pedidos = pedidos.filter(fecha_hora__date__lte=fecha_hasta)
    if estado:
        pedidos = pedidos.filter(estado=estado)

    count = pedidos.count()
    total = pedidos.aggregate(Sum('total'))['total__sum'] or 0
    promedio = round(total / count, 2) if count > 0 else 0

    return render(request, 'dashboard/reto1.html', {
        'pedidos': pedidos,
        'total': total,
        'count': count,
        'promedio': promedio,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
    })

def reto2(request):
    productos = (
        Pedido.objects.values('producto')
        .annotate(total_vendido=Sum('cantidad'))
        .order_by('-total_vendido')[:5]
    )
    max_vendido = productos[0]['total_vendido'] if productos else 1

    return render(request, 'dashboard/reto2.html', {
        'productos': productos,
        'max_vendido': max_vendido,
    })

def reto3(request):
    horas = (
        Pedido.objects.annotate(hora=ExtractHour('fecha_hora'))
        .values('hora')
        .annotate(total=Count('id'))
        .order_by('hora')
    )

    horas_data = []
    max_total = max([h['total'] for h in horas], default=1)

    for h in horas:
        total = h['total']
        if total >= 30:
            nivel = 'pico'
            color = 'danger'
        elif total >= 15:
            nivel = 'alto'
            color = 'warning'
        else:
            nivel = 'normal'
            color = 'success'

        horas_data.append({
            'hora': f"{h['hora']}:00",
            'total': total,
            'nivel': nivel,
            'color': color,
            'porcentaje': round((total / max_total) * 100),
        })

    return render(request, 'dashboard/reto3.html', {
        'horas_data': horas_data,
    })