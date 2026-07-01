# com_soc/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date


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

    role = models.CharField(max_length=20,choices=Role.choices,default=Role.REGISTADO)
    estado = models.CharField(max_length=20,choices=Estado.choices,default=Estado.POR_ATIVAR)

    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.is_staff or self.is_superuser:
            self.estado = self.Estado.ATIVADA
        super().save(*args, **kwargs)



class Subscricao(models.Model):

    class Estado(models.TextChoices):
        PENDENTE  = 'Pendente',  'Pendente'
        ATIVA     = 'Ativa',     'Ativa'
        EXPIRADA  = 'Expirada',  'Expirada'
        CANCELADA = 'Cancelada', 'Cancelada'

    class Plano(models.TextChoices):
        MENSAL = 'mensal', 'Mensal'
        ANUAL  = 'anual',  'Anual'

    utilizador = models.ForeignKey(Utilizador,on_delete=models.CASCADE,related_name='subscricoes')
    plano = models.CharField(max_length=10,choices=Plano.choices,null=True,blank=True)
    data_inicio = models.DateField(null=True, blank=True)
    data_fim    = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20,choices=Estado.choices,default=Estado.PENDENTE,)
    preco = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    # Stripe fields (new)
    stripe_customer_id     = models.CharField(max_length=100, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True, unique=True)

    class Meta:
        ordering = ['-data_inicio']

    def __str__(self):
        return f"{self.utilizador} — {self.plano} ({self.estado})"
    
    @property
    def tem_acesso(self):
        return (self.estado == self.Estado.ATIVA or (self.estado == self.Estado.CANCELADA and self.data_fim is not None and self.data_fim >= date.today()))


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
    estado_publicacao = models.CharField(max_length=20,choices=EstadoPublicacao.choices,default=EstadoPublicacao.PENDENTE)
    ai_evaluation = models.JSONField(null=True, blank=True)
    acesso = models.CharField(max_length=20, choices=Acesso.choices)
    categoria_1 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    categoria_2 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    categoria_3 = models.CharField(max_length=20, choices=Categoria.choices, null=True, blank=True)
    origem_noticia = models.CharField(max_length=20, choices=OrigemNoticia.choices, null=True, blank=True)
    editor_aprovador = models.ForeignKey(Utilizador,on_delete=models.SET_NULL, null=True,blank=True,related_name='noticias_aprovadas')
    autor = models.ForeignKey(Utilizador,on_delete=models.SET_NULL,null=True,related_name='noticias_escritas')

    def __str__(self):
        return self.titulo


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
    
    class Read(models.TextChoices):
        VISTA = 'Vista', 'Vista'
        POR_VER = 'Por_Ver', 'Por Ver'

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
    read = models.CharField(
        max_length=20,
        choices=Read.choices,
        default=Read.POR_VER
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


class ModerationConfig(models.Model):

    name = models.CharField(max_length=50, default="default")

    ai_prompt = models.TextField()

    ideal_threshold = models.PositiveSmallIntegerField(default=0)
    low_threshold = models.PositiveSmallIntegerField(default=20)
    medium_threshold = models.PositiveSmallIntegerField(default=40)
    high_threshold = models.PositiveSmallIntegerField(default=70)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
