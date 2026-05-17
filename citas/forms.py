from django import forms
from .models import Cita, HORARIOS
import datetime

DIAS_SEMANA_HABILES = [0, 1, 2, 3, 4, 5]  # lunes a sábado

class CitaForm(forms.ModelForm):
    class Meta:
        model  = Cita
        fields = ['nombre_apellido', 'telefono', 'email',
                  'tipo_solicitud', 'fecha', 'horario', 'comentarios']
        widgets = {
            'nombre_apellido': forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez'}),
            'telefono':        forms.TextInput(attrs={'placeholder': 'Ej: 2604123456'}),
            'email':           forms.EmailInput(attrs={'placeholder': 'Ej: juan@email.com'}),
            'fecha':           forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'comentarios':     forms.Textarea(attrs={'rows': 3, 'placeholder': 'Dudas o comentarios...'}),
        }

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        hoy = datetime.date.today()
        if fecha < hoy:
            raise forms.ValidationError("No podés agendar en una fecha pasada.")
        if fecha.weekday() not in DIAS_SEMANA_HABILES:
            raise forms.ValidationError("Solo se atiende de lunes a sábado.")
        return fecha

    def clean(self):
        cleaned = super().clean()
        fecha   = cleaned.get('fecha')
        horario = cleaned.get('horario')
        if fecha and horario:
            if Cita.objects.filter(fecha=fecha, horario=horario).exists():
                raise forms.ValidationError("Ese turno ya está ocupado. Elegí otro horario.")
        return cleaned