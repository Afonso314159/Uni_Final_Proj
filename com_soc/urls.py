from django.urls import path

from . import views

urlpatterns = [
    # ex: /com_soc/
    path("", views.home, name="home"),
    # Subscriber page - premium news + chat
    path("subscriber/", views.subscriber, name="subscriber"),
    # Subscription advertisement page
    path("subscribe/", views.sub_ad, name="sub_ad"),
    # Subscription advertisement page
    path("editor/", views.editor, name="editor"),
    path('noticia/<int:id>/aceitar/', views.aceitar_noticia, name='aceitar_noticia'),
    path('noticia/<int:id>/eliminar/', views.eliminar_noticia, name='eliminar_noticia'),
    path('noticia/<int:id>/json/', views.noticia_json, name='noticia_json'),
    path('noticia/<int:id>/editar/', views.editar_noticia, name='editar_noticia'),
    # News detail page
    path("noticia/<int:noticia_id>/", views.noticia_detail, name="noticia"),
    # Comments
    path("noticia/<int:noticia_id>/comment/", views.add_comment, name="add_comment"),
    # Create news
    path("noticia/create/", views.create_noticia, name="create_noticia"),
]