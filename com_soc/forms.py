from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilizador

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Utilizador
        fields = ["username","email","password1","password2"]