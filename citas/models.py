from django.db import models

TIPO_SOLICITUD = [
    ('consulta', 'Consulta'),
    ('tramite', 'Cita para trámite'),
]

HORARIOS = [
    ('09:00', '9:00 hs'),
    ('10:00', '10:00 hs'),
    ('11:00', '11:00 hs'),
    ('12:00', '12:00 hs'),
]

class Cita(models.Model):
    nombre_apellido = models.CharField(max_length=100)
    telefono        = models.CharField(max_length=30)
    email           = models.EmailField()
    tipo_solicitud  = models.CharField(max_length=20, choices=TIPO_SOLICITUD)
    fecha           = models.DateField()
    horario         = models.CharField(max_length=10, choices=HORARIOS)
    comentarios     = models.TextField(blank=True)
    creada_en       = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('fecha', 'horario')
        ordering = ['fecha', 'horario']

    def __str__(self):
        return f"{self.nombre_apellido} — {self.fecha} {self.horario}"


class Resena(models.Model):
    nombre    = models.CharField(max_length=50)
    apellido  = models.CharField(max_length=50)
    mensaje   = models.TextField(max_length=500)
    respuesta = models.TextField(blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creada_en']

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


HORARIOS_OPCIONALES = [('', 'Día completo')] + HORARIOS

class BloqueoAgenda(models.Model):
    fecha   = models.DateField()
    horario = models.CharField(max_length=10, choices=HORARIOS_OPCIONALES, blank=True)
    motivo  = models.CharField(max_length=200, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha', 'horario']
        unique_together = ('fecha', 'horario')  # evita duplicados

    def es_dia_completo(self):
        return self.horario == ''

    def __str__(self):
        if self.es_dia_completo():
            return f"{self.fecha} — Día completo — {self.motivo or 'Sin motivo'}"
        return f"{self.fecha} {self.horario} — {self.motivo or 'Sin motivo'}"

# --------------Notificaciones del navegador ----------------------

class PushSuscripcion(models.Model):
    endpoint  = models.TextField(unique=True)
    p256dh    = models.TextField()
    auth      = models.TextField()
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.endpoint[:60]