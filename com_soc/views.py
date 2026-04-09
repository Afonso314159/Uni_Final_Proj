# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Noticia
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from django.contrib.auth import login, logout, authenticate

def landing_page(request):
    return render(request, "com_soc/landing_page.html") # A simple page with a "Enter Site" or "Login" button

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('/com_soc')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {"form": form})

@login_required
def home(request):
    latest_noticia_list = Noticia.objects.order_by("-data_criacao")[:5]
    context = {"latest_noticia_list": latest_noticia_list}
    return render(request, "com_soc/home.html", context)

def noticia(request, noticia_id):
    return HttpResponse("You're looking at noticia %s." % noticia_id)


def comentario(request, noticia_id):
    response = "You're looking at the comment of noticia %s."
    return HttpResponse(response % noticia_id)
