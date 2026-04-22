from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilizador, Noticia

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Utilizador
        fields = ["username","email","password1","password2"]

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'corpo_texto', 'categoria_2']