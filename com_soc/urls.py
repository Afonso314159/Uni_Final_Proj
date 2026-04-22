from django.urls import path

from . import views

urlpatterns = [
    # ex: /com_soc/
    path("", views.home, name="home"),
    # Subscriber page - premium news + chat
    path("subscriber/", views.subscriber, name="subscriber"),
    # Subscription advertisement page
    path("subscribe/", views.sub_ad, name="sub_ad"),
    # News detail page
    path("noticia/<int:noticia_id>/", views.noticia_detail, name="noticia"),
    # Comments
    path("noticia/<int:noticia_id>/comment/", views.add_comment, name="add_comment"),
    # Create news
    path("noticia/create/", views.create_noticia, name="create_noticia"),
]