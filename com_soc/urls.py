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
    #notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/delete/<int:id>/', views.delete_notification, name='delete_notification'),
    path('notifications/delete-all/', views.delete_all_notifications, name='delete_all_notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    # Create news
    path("noticia/create/", views.create_noticia, name="create_noticia"),
    path('verification-pending/', views.verification_pending, name='verification_pending'),
    path('account-blocked/', views.account_blocked, name='account_blocked'),
    #definicoes
    path('definicoes/', views.definicoes, name='definicoes'),
    path('account/', views.account, name='account'),
    path('account/avatar/', views.update_avatar, name='update_avatar'),
    path('account/username/', views.update_username, name='update_username'),
    path('account/password/', views.change_password, name='change_password'),
]