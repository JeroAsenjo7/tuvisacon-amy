from django.shortcuts import render
from citas.models import Resena

def home(request):
    resenas = Resena.objects.all()[:6]
    return render(request, 'landing/home.html', {'resenas': resenas})
