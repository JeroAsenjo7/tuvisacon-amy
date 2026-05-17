from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('reservar/',                                    views.reservar_cita,    name='reservar_cita'),
    path('confirmada/',                                  views.cita_confirmada,  name='cita_confirmada'),
    path('panel/',                                       views.panel_citas,      name='panel_citas'),
    path('login/',  auth_views.LoginView.as_view(template_name='citas/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'),                   name='logout'),
    path('panel/eliminar/<int:cita_id>/',               views.eliminar_cita,    name='eliminar_cita'),
    path('resenas/crear/',                               views.crear_resena,     name='crear_resena'),
    path('panel/resenas/eliminar/<int:resena_id>/',      views.eliminar_resena,  name='eliminar_resena'),
    path('panel/resenas/responder/<int:resena_id>/',     views.responder_resena, name='responder_resena'),
    # Días bloqueados
    path('panel/bloquear-dia/',                      views.bloquear_dia,  name='bloquear_dia'),
    path('panel/desbloquear/<int:bloqueo_id>/',       views.desbloquear,   name='desbloquear'),
    # Notificaciones del navegador 
    path('push/public-key/', views.vapid_public_key,    name='vapid_public_key'),
    path('push/suscribir/',  views.guardar_suscripcion, name='guardar_suscripcion'),
]