from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from .models import Noticia, Comentario, ImagemNoticia
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, NoticiaForm
from django.contrib.auth import login, logout, authenticate
from .decorators import admin_required, sub_required, editor_required
from django.utils import timezone
from .utils import AI_score
import json


def landing_page(request):

    if request.user.is_authenticated:
        return redirect('home')

    all_news = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA
    ).order_by("-data_publicacao", "-data_criacao")[:6]

    featured_news = None
    side_news = []

    for news in all_news:
        if featured_news is None and news.imagens.exists():
            featured_news = news
        else:
            side_news.append(news)
        if len(side_news) >= 5:
            break

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
            login(request, user)
            return redirect('/com_soc')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {"form": form})


@login_required
def home(request):
    news_list = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        acesso=Noticia.Acesso.PUBLICO
    ).order_by("-data_publicacao", "-data_criacao")

    context = {
        "news_list": news_list,
        "page_type": "home",
        "page_title": "Notícias Públicas",
        "page_subtitle": "Últimas notícias de acesso público",
    }
    return render(request, "com_soc/home.html", context)


@sub_required
def subscriber(request):
    news_list = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        acesso=Noticia.Acesso.PREMIUM
    ).order_by("-data_publicacao", "-data_criacao")

    context = {
        "news_list": news_list,
        "page_type": "subscriber",
        "page_title": "Notícias Exclusivas",
        "page_subtitle": "Conteúdo exclusivo para subscritores",
    }
    return render(request, "com_soc/subscriber.html", context)


@login_required
def sub_ad(request):
    if request.user.role == 'Subscritor':
        return redirect('subscriber')
    context = {
        'page_type': 'sub_ad',
        'page_title': 'Subscrição',
    }
    return render(request, "com_soc/sub_ad.html", context)


@editor_required
def editor(request):
    pendentes = list(
        Noticia.objects.filter(
            estado_publicacao=Noticia.EstadoPublicacao.PENDENTE,
        ).order_by("-data_publicacao", "-data_criacao")
    )

    publicadas = list(
        Noticia.objects.filter(
            estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        ).order_by("-data_publicacao", "-data_criacao")
    )

    # Serialize ai_evaluation to a JSON string so templates can embed it
    # safely in data attributes via the |escape filter.
    for news in pendentes:
        news._ai_json = json.dumps(news.ai_evaluation) if news.ai_evaluation else ''
    for news in publicadas:
        news._ai_json = json.dumps(news.ai_evaluation) if news.ai_evaluation else ''

    context = {
        'pendentes': pendentes,
        'publicadas': publicadas,
        'page_type': 'editor',
        'page_title': 'Editor',
    }
    return render(request, "com_soc/editor.html", context)


@editor_required
@require_POST
def aceitar_noticia(request, id):
    noticia = get_object_or_404(Noticia, id=id)
    noticia.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
    noticia.data_publicacao = timezone.now().date()
    noticia.editor_aprovador = request.user
    noticia.save()
    return JsonResponse({'success': True})


@editor_required
@require_POST
def eliminar_noticia(request, id):
    noticia = get_object_or_404(Noticia, id=id)
    noticia.delete()
    return JsonResponse({'success': True})


@login_required
def noticia_detail(request, noticia_id):
    noticia = get_object_or_404(Noticia, pk=noticia_id)

    user_is_editor = (request.user.is_staff or request.user.is_superuser)
    user_is_subscriber = (request.user.role == 'Subscritor' or user_is_editor)

    if noticia.acesso == Noticia.Acesso.PREMIUM:
        if not user_is_subscriber:
            return redirect('sub_ad')

    if noticia.estado_publicacao == Noticia.EstadoPublicacao.PENDENTE:
        if not user_is_editor:
            return redirect('home')

    comments = []
    if user_is_subscriber:
        comments = noticia.comentarios.filter(
            estado=Comentario.Estado.NORMAL
        ).select_related('utilizador').order_by('-data_post')

    context = {
        "news": noticia,
        "comments": comments,
        "user_is_subscriber": user_is_subscriber,
    }
    return render(request, "com_soc/noticia.html", context)


@require_POST
@sub_required
def add_comment(request, noticia_id):
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
    form = NoticiaForm(request.POST, is_staff=request.user.is_staff or request.user.is_superuser)
    if not form.is_valid():
        return JsonResponse({"success": False, "error": form.errors}, status=400)

    noticia_obj = form.save(commit=False)
    noticia_obj.autor = request.user
    noticia_obj.acesso = request.POST.get('acesso', 'publico')
    noticia_obj.categoria_1 = request.POST.get('categoria_1') or None
    noticia_obj.categoria_2 = request.POST.get('categoria_2') or None
    noticia_obj.categoria_3 = request.POST.get('categoria_3') or None
    noticia_obj.data_criacao = timezone.now().date()

    user_editor_or_admin = (request.user.is_staff or request.user.is_superuser)

    if user_editor_or_admin:
        # Editors and admins bypass AI review entirely
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
        noticia_obj.data_publicacao = timezone.now().date()
        noticia_obj.editor_aprovador = request.user
        noticia_obj.save()
    else:
        # Regular users: run through AI moderation pipeline
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PRE_AI
        noticia_obj.origem_noticia = Noticia.OrigemNoticia.NOTICIAS_DO_POVO
        noticia_obj.acesso = Noticia.Acesso.PUBLICO
        noticia_obj.save()

        evaluation = AI_score(noticia_obj)
        noticia_obj.ai_evaluation = evaluation
        risk_level = evaluation.get('risk_level', 'medium')

        if risk_level == 'trash':
            # Content is too harmful / low quality — reject immediately, no review needed
            noticia_obj.delete()
            return JsonResponse({
                "success": False,
                "rejected": True,
                "error": (
                    "O teu artigo foi rejeitado automaticamente por não cumprir "
                    "os critérios mínimos de qualidade e/ou conter conteúdo impróprio."
                ),
            })

        elif risk_level == 'ideal':
            # Both scores are 0 — auto-publish, no human review needed
            noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
            noticia_obj.data_publicacao = timezone.now().date()

        else:
            # low / medium / high — send to editor queue for human review
            noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PENDENTE

        noticia_obj.save()

    for imagem in request.FILES.getlist("imagens"):
        ImagemNoticia.objects.create(noticia=noticia_obj, imagem=imagem)

    return JsonResponse({"success": True})


@editor_required
def noticia_json(request, id):
    noticia = get_object_or_404(Noticia, pk=id)
    return JsonResponse({
        'titulo': noticia.titulo,
        'corpo_texto': noticia.corpo_texto,
        'acesso': noticia.acesso,
        'categoria_1': noticia.categoria_1 or '',
        'categoria_2': noticia.categoria_2 or '',
        'categoria_3': noticia.categoria_3 or '',
        'ai_evaluation': noticia.ai_evaluation,
        'imagens': [
            {'url': img.imagem.url, 'id': img.id}
            for img in noticia.imagens.all()
        ],
    })


@editor_required
@require_POST
def editar_noticia(request, id):
    noticia = get_object_or_404(Noticia, pk=id)
    form = NoticiaForm(request.POST, instance=noticia, is_staff=True)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': form.errors}, status=400)
    form.save()
    return JsonResponse({'success': True})