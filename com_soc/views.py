# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Noticia, Comentario, ImagemNoticia
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from django.contrib.auth import login, logout, authenticate
from .decorators import admin_required, sub_required, editor_required
from django.utils import timezone
import json



def landing_page(request):
    # Get published news, prioritize ones with images for the featured spot
    all_news = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA
    ).order_by("-data_publicacao", "-data_criacao")[:6]
    
    # Find a featured news (one with an image) for the center spot
    featured_news = None
    side_news = []
    
    for news in all_news:
        if featured_news is None and news.imagens.exists():
            featured_news = news
        else:
            side_news.append(news)
        if len(side_news) >= 5:
            break
    
    # If no news with image, use first news as featured
    if featured_news is None and all_news.exists():
        featured_news = all_news.first()
        side_news = list(all_news[1:6])
    
    context = {
        "featured_news": featured_news,
        "side_news": side_news,
    }
    return render(request, "com_soc/landing_page.html", context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('/com_soc')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {"form": form})

@login_required
def home(request):
    """Home page - shows only PUBLIC news"""
    news_list = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        categoria=Noticia.CategoriaAcesso.PUBLICO
    ).order_by("-data_publicacao", "-data_criacao")
    
    context = {
        "news_list": news_list,
        "page_type": "home",
        "page_title": "Notícias Públicas",
        "page_subtitle": "Últimas notícias de acesso público"
    }
    return render(request, "com_soc/home.html", context)


@sub_required
def subscriber(request):
    """Subscriber page - shows only PREMIUM news"""
    news_list = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        categoria=Noticia.CategoriaAcesso.PREMIUM
    ).order_by("-data_publicacao", "-data_criacao")
    
    context = {
        "news_list": news_list,
        "page_type": "subscriber",
        "page_title": "Notícias Exclusivas",
        "page_subtitle": "Conteúdo exclusivo para subscritores"
    }
    return render(request, "com_soc/subscriber.html", context)

@login_required
def sub_ad(request):
    """Subscription advertisement page for non-subscribers"""
    if request.user.role == 'Subscritor':
        return redirect('subscriber')
    context = {
        "page_type": "sub_ad",
        "page_title": "Subscrever",
    }
    return render(request, "com_soc/sub_ad.html", context)


@login_required
def noticia(request, noticia_id):
    """News page - minimal placeholder for now"""

    noticia = get_object_or_404(Noticia, pk=noticia_id)

    user_is_subscriber = (request.user.role == 'Subscritor' or request.user.is_staff or request.user.is_superuser)

    if noticia.categoria == 'Premium':
        if not user_is_subscriber:
            return redirect('sub_ad')
    
    comments = []
    if user_is_subscriber:
        comments = noticia.comentarios.filter(
            estado=noticia.comentarios.model.Estado.NORMAL
        ).select_related('utilizador').order_by('-data_post')
    
    if user_is_subscriber:
        back_url = "/com_soc/subscriber"
        back_label = "Voltar"
    else:
        back_url = "/com_soc"
        back_label = "Voltar"

    context = {
        "news": noticia,
        "comments": comments,
        "user_is_subscriber": user_is_subscriber,
        "page_type": "noticia",
        "back_url": back_url,
        "back_label": back_label,
    }
    return render(request, "com_soc/noticia.html", context)


@require_POST
@sub_required
def add_comment(request, noticia_id):
    """Add a comment to a news article (subscribers only)."""
    noticia_obj = get_object_or_404(Noticia, pk=noticia_id)
    conteudo = request.POST.get("conteudo", "").strip()

    if not conteudo:
        return JsonResponse({"success": False, "error": "Comentário vazio."}, status=400)

    comment = Comentario.objects.create(
        noticia=noticia_obj,
        utilizador=request.user,
        conteudo=conteudo,
    )

    return JsonResponse({
        "success": True,
        "comment": {
            "id": comment.id,
            "author": comment.utilizador.username,
            "conteudo": comment.conteudo,
        }
    })


@require_POST
@login_required
def create_noticia(request):
    """Create a news article. Any logged-in user can submit; goes straight to DB."""
    titulo = request.POST.get("titulo", "").strip()
    corpo_texto = request.POST.get("corpo_texto", "").strip()

    if not titulo or len(corpo_texto) < 20:
        return JsonResponse({"success": False, "error": "Título ou descrição inválidos."}, status=400)

    noticia_obj = Noticia.objects.create(
        titulo=titulo,
        corpo_texto=corpo_texto,
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        data_publicacao=timezone.now().date(),
        categoria=Noticia.CategoriaAcesso.PUBLICO,
        autor=request.user,
        editor_aprovador=request.user,
    )

    for imagem in request.FILES.getlist("imagens"):
        ImagemNoticia.objects.create(noticia=noticia_obj, imagem=imagem)

    return JsonResponse({"success": True, "id": noticia_obj.id})