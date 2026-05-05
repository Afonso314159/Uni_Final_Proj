# com_soc/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser


class Utilizador(AbstractUser):
    class Role(models.TextChoices):
        REGISTADO = 'Registado', 'Registado'
        SUBSCRITOR = 'Subscritor', 'Subscritor'
        EDITOR = 'Editor', 'Editor'
        ADMIN = 'Admin', 'Admin'

    class Estado(models.TextChoices):
        POR_ATIVAR = 'Por_Ativar', 'Por Ativar'
        ATIVADA = 'Ativada', 'Ativada'
        BLOQUEADA = 'Bloqueada', 'Bloqueada'
        ELIMINADO = 'Eliminado', 'Eliminado'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.REGISTADO
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.POR_ATIVAR
    )

    # username, email, password, date_joined already exist in AbstractUser


class Subscricao(models.Model):
    class Estado(models.TextChoices):
        ATIVA = 'Ativa', 'Ativa'
        EXPIRADA = 'Expirada', 'Expirada'

    utilizador = models.ForeignKey(
        Utilizador,
        on_delete=models.CASCADE,
        related_name='subscricoes'
    )
    data_inicio = models.DateField()
    data_fim = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
    )
    preco = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)


class Noticia(models.Model):

    class EstadoPublicacao(models.TextChoices):
        PRE_AI    = 'pre_ai',    'Pré-AI'
        PENDENTE  = 'pendente',  'Pendente'
        PUBLICADA = 'publicada', 'Publicada'

    class Categoria(models.TextChoices):
        POLITICA      = 'politica',      'Política'
        ECONOMIA      = 'economia',      'Economia'
        TECNOLOGIA    = 'tecnologia',    'Tecnologia'
        CIENCIA       = 'ciencia',       'Ciência'
        EDUCACAO      = 'educacao',      'Educação'
        INTERNACIONAL = 'internacional', 'Internacional'
        NACIONAL      = 'nacional',      'Nacional'
        DESPORTO      = 'desporto',      'Desporto'
        CULTURA       = 'cultura',       'Cultura'
        MARITIMO      = 'maritimo',      'Marítimo'

    class Acesso(models.TextChoices):
        PUBLICO = 'publico', 'Público'
        PREMIUM = 'premium', 'Premium'

    class OrigemNoticia(models.TextChoices):
        NOTICIAS_DO_POVO = 'noticias_do_povo', 'Notícias do Povo'

    titulo = models.CharField(max_length=255)
    corpo_texto = models.TextField()
    data_criacao = models.DateField(auto_now_add=True)
    data_publicacao = models.DateField(null=True, blank=True)
    estado_publicacao = models.CharField(
        max_length=20,
        choices=EstadoPublicacao.choices,
        default=EstadoPublicacao.PENDENTE
    )
    ai_score = models.FloatField(null=True, blank=True)
    acesso = models.CharField(max_length=20, choices=Acesso.choices)
    categoria_1 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    categoria_2 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    categoria_3 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    origem_noticia = models.CharField(max_length=20, choices=OrigemNoticia.choices, null=True, blank=True)
    editor_aprovador = models.ForeignKey(
        Utilizador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='noticias_aprovadas'
    )
    autor = models.ForeignKey(
        Utilizador,
        on_delete=models.SET_NULL,
        null=True,
        related_name='noticias_escritas'
    )


class ImagemNoticia(models.Model):
    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
        related_name='imagens'
    )
    imagem = models.ImageField(upload_to='noticias/')
    legenda = models.CharField(max_length=255, blank=True)
    ordem = models.IntegerField(null=True, blank=True)


class Comentario(models.Model):
    class Estado(models.TextChoices):
        NORMAL = 'Normal', 'Normal'
        REPORTADA = 'Reportada', 'Reportada'
        APAGADA = 'Apagada', 'Apagada'

    noticia = models.ForeignKey(
        Noticia,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    utilizador = models.ForeignKey(
        Utilizador,
        on_delete=models.CASCADE,
        related_name='comentarios'
    )
    conteudo = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NORMAL
    )
    data_post = models.DateTimeField(auto_now_add=True)


class Notificacao(models.Model):
    class Estado(models.TextChoices):
        NORMAL = 'Normal', 'Normal'
        APAGADA = 'Apagada', 'Apagada'

    utilizador = models.ForeignKey(
        Utilizador,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    conteudo = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NORMAL
    )
    timestamp = models.DateTimeField(auto_now_add=True)


class ChatMensagem(models.Model):
    class Estado(models.TextChoices):
        NORMAL = 'Normal', 'Normal'
        REPORTADA = 'Reportada', 'Reportada'
        APAGADA = 'Apagada', 'Apagada'

    utilizador = models.ForeignKey(
        Utilizador,
        on_delete=models.CASCADE,
        related_name='mensagens'
    )
    conteudo = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NORMAL
    )
    timestamp = models.DateTimeField(auto_now_add=True)