from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Utilizador, Subscricao, Noticia, ImagemNoticia,
    Comentario, Notificacao, ChatMensagem
)

class UtilizadorAdmin(UserAdmin):
    # adds role and estado to the bottom of the user edit page
    fieldsets = UserAdmin.fieldsets + (
        ('Informação Extra', {'fields': ('role', 'estado')}),
    )

admin.site.register(Utilizador, UtilizadorAdmin)
admin.site.register(Subscricao)
admin.site.register(Noticia)
admin.site.register(ImagemNoticia)
admin.site.register(Comentario)
admin.site.register(Notificacao)
admin.site.register(ChatMensagem)