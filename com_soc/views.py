from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def noticia(request, noticia_id):
    return HttpResponse("You're looking at noticia %s." % noticia_id)



def comentario(request, noticia_id):
    response = "You're looking at the comment of noticia %s."
    return HttpResponse(response % noticia_id)
