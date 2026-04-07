from django.urls import path

from . import views

urlpatterns = [
    # ex: /noticia/
    path("", views.index, name="index"),
    # ex: /noticia/5/
    path("<int:noticia_id>/", views.noticia, name="noticia"),
    # ex: /noticia/5/comentario/
    path("<int:noticia_id>/comentario/", views.comentario, name="comentario"),
]