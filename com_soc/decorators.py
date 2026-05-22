from django.shortcuts import redirect
from functools import wraps
from .models import Utilizador
from django.contrib.auth import logout

def authenticated_user(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.estado == Utilizador.Estado.POR_ATIVAR:
            logout(request)
            return redirect('verification_pending')
        if request.user.estado in (Utilizador.Estado.BLOQUEADA, Utilizador.Estado.ELIMINADO):
            logout(request)
            return redirect('account_blocked')
        return view_func(request, *args, **kwargs)
    return wrapper

def sub_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'Subscritor' or request.user.is_staff or request.user.is_superuser):
            return redirect('sub_ad')
        return view_func(request, *args, **kwargs)
    return wrapper

def editor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper