from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Cita, Resena, BloqueoAgenda, HORARIOS, PushSuscripcion
from .forms import CitaForm
import datetime
# notificaciones del navegador
import json
from pywebpush import webpush, WebPushException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
 
def reservar_cita(request):
    turnos_ocupados = list(Cita.objects.values_list('fecha', 'horario'))
    turnos_ocupados_str = [
        f"{f.strftime('%Y-%m-%d')}_{h}" for f, h in turnos_ocupados
    ]

    bloqueos = BloqueoAgenda.objects.all()
    dias_bloqueados_completos = [
        b.fecha.strftime('%Y-%m-%d')
        for b in bloqueos if b.es_dia_completo()
    ]
    turnos_bloqueados = [
        f"{b.fecha.strftime('%Y-%m-%d')}_{b.horario}"
        for b in bloqueos if not b.es_dia_completo()
    ]
    # Unir turnos ocupados por citas + turnos bloqueados manualmente
    todos_ocupados = turnos_ocupados_str + turnos_bloqueados

    if request.method == 'POST':
        form = CitaForm(request.POST)
        if form.is_valid():
            fecha_elegida  = str(form.cleaned_data['fecha'])
            horario_elegido = form.cleaned_data['horario']
            if fecha_elegida in dias_bloqueados_completos:
                form.add_error('fecha', 'Este día no está disponible.')
            elif f"{fecha_elegida}_{horario_elegido}" in turnos_bloqueados:
                form.add_error('horario', 'Este horario no está disponible.')
            else:
                cita = form.save()
                notificar_push(cita)
                messages.success(request, '¡Cita agendada! Amaly se contactará pronto.')
                return redirect('cita_confirmada')
    else:
        form = CitaForm()

    return render(request, 'citas/reservar.html', {
        'form':                       form,
        'turnos_ocupados':            todos_ocupados,
        'dias_bloqueados':            dias_bloqueados_completos,
    })


def cita_confirmada(request):
    return render(request, 'citas/confirmada.html')


@login_required
def panel_citas(request):
    hoy = datetime.date.today()
    fecha_filtro = request.GET.get('fecha', '')
    mes_filtro   = request.GET.get('mes', '')

    proximas = Cita.objects.filter(fecha__gte=hoy)
    pasadas  = Cita.objects.filter(fecha__lt=hoy)

    if fecha_filtro:
        try:
            fecha_obj = datetime.date.fromisoformat(fecha_filtro)
            proximas = proximas.filter(fecha=fecha_obj)
            pasadas  = pasadas.filter(fecha=fecha_obj)
        except ValueError:
            pass
    elif mes_filtro:
        try:
            anio, mes = mes_filtro.split('-')
            proximas = proximas.filter(fecha__year=anio, fecha__month=mes)
            pasadas  = pasadas.filter(fecha__year=anio, fecha__month=mes)
        except ValueError:
            pass

    resenas  = Resena.objects.all()
    bloqueos = BloqueoAgenda.objects.filter(fecha__gte=hoy)

    return render(request, 'citas/panel.html', {
        'proximas':        proximas,
        'pasadas':         pasadas,
        'fecha_filtro':    fecha_filtro,
        'mes_filtro':      mes_filtro,
        'resenas':         resenas,
        'bloqueos':        bloqueos,
        'vapid_public_key': settings.VAPID_PUBLIC_KEY,
    })


@login_required
def bloquear_dia(request):
    if request.method == 'POST':
        fecha   = request.POST.get('fecha', '').strip()
        horario = request.POST.get('horario', '').strip()
        motivo  = request.POST.get('motivo', '').strip()
        if fecha:
            try:
                fecha_obj = datetime.date.fromisoformat(fecha)
                obj, created = BloqueoAgenda.objects.get_or_create(
                    fecha=fecha_obj,
                    horario=horario,
                    defaults={'motivo': motivo}
                )
                if created:
                    if horario:
                        label = dict(HORARIOS).get(horario, horario)
                        messages.success(request, f'Turno {label} del {fecha_obj.strftime("%d/%m/%Y")} bloqueado.')
                    else:
                        messages.success(request, f'Día {fecha_obj.strftime("%d/%m/%Y")} bloqueado completo.')
                else:
                    messages.error(request, 'Ese bloqueo ya existe.')
            except ValueError:
                messages.error(request, 'Fecha inválida.')
        else:
            messages.error(request, 'Seleccioná una fecha.')
    return redirect('panel_citas')


@login_required
def desbloquear(request, bloqueo_id):
    if request.method == 'POST':
        bloqueo = get_object_or_404(BloqueoAgenda, id=bloqueo_id)
        bloqueo.delete()
        messages.success(request, 'Bloqueo eliminado.')
    return redirect('panel_citas')

@login_required
def eliminar_cita(request, cita_id):
    if request.method == 'POST':
        cita = get_object_or_404(Cita, id=cita_id)
        cita.delete()
        messages.success(request, 'Turno eliminado y liberado.')
    return redirect('panel_citas')


# ── Reseñas ──────────────────────────────────────────────

def crear_resena(request):
    if request.method == 'POST':
        nombre  = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        mensaje = request.POST.get('mensaje', '').strip()
        if nombre and apellido and mensaje:
            Resena.objects.create(nombre=nombre, apellido=apellido, mensaje=mensaje)
            messages.success(request, '¡Gracias por tu reseña!')
        else:
            messages.error(request, 'Completá todos los campos.')
    return redirect('/')          # ajustá si tu landing tiene otro name


@login_required
def eliminar_resena(request, resena_id):
    if request.method == 'POST':
        resena = get_object_or_404(Resena, id=resena_id)
        resena.delete()
        messages.success(request, 'Reseña eliminada.')
    return redirect('panel_citas')


@login_required
def responder_resena(request, resena_id):
    if request.method == 'POST':
        resena = get_object_or_404(Resena, id=resena_id)
        resena.respuesta = request.POST.get('respuesta', '').strip()
        resena.save()
        messages.success(request, 'Respuesta guardada.')
    return redirect('panel_citas')

def agregar_resena(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        texto  = request.POST.get('texto', '').strip()
        if nombre and texto:
            Resena.objects.create(nombre=nombre, texto=texto)
            messages.success(request, '¡Gracias por tu reseña!')
        return redirect('home')
    return redirect('home')

# --Notifaciones del navegador -------
def vapid_public_key(request):
    return JsonResponse({'public_key': settings.VAPID_PUBLIC_KEY})


@csrf_exempt
def guardar_suscripcion(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            PushSuscripcion.objects.update_or_create(
                endpoint=data['endpoint'],
                defaults={
                    'p256dh': data['keys']['p256dh'],
                    'auth':   data['keys']['auth'],
                }
            )
            return JsonResponse({'ok': True})
        except Exception as e:
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    return JsonResponse({'ok': False}, status=405)


def notificar_push(cita):
    import os
    suscripciones = PushSuscripcion.objects.all()
    
    # Si existe el archivo .pem lo usa, sino usa la variable de entorno
    pem_path = os.path.join(settings.BASE_DIR, 'private_key.pem')
    if os.path.exists(pem_path):
        vapid_key = pem_path
    else:
        vapid_key = settings.VAPID_PRIVATE_KEY

    for s in suscripciones:
        try:
            webpush(
                subscription_info={
                    'endpoint': s.endpoint,
                    'keys': {'p256dh': s.p256dh, 'auth': s.auth}
                },
                data=json.dumps({
                    'title': '📅 Nueva cita agendada',
                    'body':  f"{cita.nombre_apellido} · {cita.fecha.strftime('%d/%m/%Y')} {cita.horario} hs",
                }),
                vapid_private_key=vapid_key,
                vapid_claims=settings.VAPID_CLAIMS,
            )
        except WebPushException as e:
            print(f"Error push: {e}")