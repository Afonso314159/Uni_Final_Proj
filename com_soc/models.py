from django.db import models

# Create your models here.
class Noticia(models.Model):
    noticia_texto = models.CharField(max_length=5000)
    data_criacao = models.DateTimeField("Data em que foi criada", auto_now_add=True)

    def __str__(self):
        return self.noticia_texto

class Comentario(models.Model):

    noticia = models.ForeignKey(Noticia, on_delete=models.CASCADE)
    comentario_texto = models.CharField(max_length=500)
    data_publicacao = models.DateTimeField("Data em que foi publicado", auto_now_add=True)

    def __str__(self):
        return self.comentario_texto