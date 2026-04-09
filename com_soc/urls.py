from django.urls import path

from . import views

urlpatterns = [
    # ex: /com_soc/
    path("", views.home, name="home"),
    # ex: /noticom_soccia/5/
    path("<int:noticia_id>/", views.noticia, name="noticia"),
    # ex: /com_soc/5/comentario/
    path("<int:noticia_id>/comentario/", views.comentario, name="comentario"),
]