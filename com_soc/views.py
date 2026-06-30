from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.core.paginator import Paginator  
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from .models import Noticia, Comentario, ImagemNoticia, Utilizador, Notificacao, ModerationConfig
from .forms import RegisterForm, NoticiaForm
from .decorators import admin_required, sub_required, editor_required, authenticated_user
from .utils import AI_score, email_verification_token, send_verification_email, create_notification
from .tasks import evaluate_noticia_task
import json


# ---------------------------------------------------------------------------
# Landing & Auth
# ---------------------------------------------------------------------------

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
            user = form.save(commit=False)
            user.is_active = False          # block login until email verified
            user.save()
            try:
                send_verification_email(request, user)
            except Exception:
                # Email failed to send — delete the user so they can try again
                user.delete()
                form.add_error(None, 'Não foi possível enviar o email de verificação. Tenta novamente.')
                return render(request, 'registration/register.html', {"form": form})
            return render(request, 'registration/verification_sent.html', {'email': user.email})
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {"form": form})


def verify_email(request, uidb64, token):
    """
    Handles the one-time email verification link.
    On success: activates the account, logs the user in, redirects to home.
    On failure: shows an invalid/expired link page.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilizador.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilizador.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.estado = Utilizador.Estado.ATIVADA
        user.save()
        login(request, user)
        return redirect('home')

    return render(request, 'registration/verification_invalid.html')

def verification_pending(request):
    return render(request, 'registration/verification_sent.html')

def account_blocked(request):
    return render(request, 'registration/account_blocked.html')


# ---------------------------------------------------------------------------
# Main pages
# ---------------------------------------------------------------------------

CATEGORIES = Noticia.Categoria.choices
NEWS_PER_PAGE = 10

@authenticated_user
def home(request):
    qs = Noticia.objects.filter(
        estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        acesso=Noticia.Acesso.PUBLICO,
    ).order_by("-data_publicacao", "-data_criacao")
 
    # ---- filters ----
    q          = request.GET.get("q", "")
    date_from  = request.GET.get("date_from", "").strip()
    date_to    = request.GET.get("date_to", "").strip()
    cats       = request.GET.getlist("cat")          # up to 3 values
    cats       = [c for c in cats if c]              # drop empties
 
    if q.strip():
        qs = qs.filter(titulo__icontains=q.strip())
    if date_from:
        qs = qs.filter(data_publicacao__gte=date_from)
    if date_to:
        qs = qs.filter(data_publicacao__lte=date_to)
    if cats:
        from django.db.models import Q
        cat_q = Q()
        for c in cats:
            cat_q |= Q(categoria_1=c) | Q(categoria_2=c) | Q(categoria_3=c)
        qs = qs.filter(cat_q)
 
    filter_active = bool(q.strip() or date_from or date_to or cats)
 
    # ---- pagination ----
    paginator   = Paginator(qs, NEWS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj    = paginator.get_page(page_number)
 
    context = {
        "news_list":           page_obj,
        "page_obj":            page_obj,
        "page_type":           "home",
        "page_title":          "Notícias Públicas",
        "page_subtitle":       "Últimas notícias de acesso público",
        # filter state — sent back so inputs stay filled
        "filter_q":            q,
        "filter_date_from":    date_from,
        "filter_date_to":      date_to,
        "filter_cats":         cats,
        "filter_active":       filter_active,
        "categories":          CATEGORIES,
    }
    return render(request, "com_soc/home.html", context)
 
 
@authenticated_user
@sub_required
def subscriber(request):
    # start with premium only; optionally include public
    include_public = request.GET.get("include_public") == "1"
 
    if include_public:
        qs = Noticia.objects.filter(
            estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
        )
    else:
        qs = Noticia.objects.filter(
            estado_publicacao=Noticia.EstadoPublicacao.PUBLICADA,
            acesso=Noticia.Acesso.PREMIUM,
        )
 
    qs = qs.order_by("-data_publicacao", "-data_criacao")
 
    # ---- filters ----
    q          = request.GET.get("q", "")
    date_from  = request.GET.get("date_from", "").strip()
    date_to    = request.GET.get("date_to", "").strip()
    cats       = request.GET.getlist("cat")
    cats       = [c for c in cats if c]
 
    if q.strip():
        qs = qs.filter(titulo__icontains=q.strip())
    if date_from:
        qs = qs.filter(data_publicacao__gte=date_from)
    if date_to:
        qs = qs.filter(data_publicacao__lte=date_to)
    if cats:
        from django.db.models import Q
        cat_q = Q()
        for c in cats:
            cat_q |= Q(categoria_1=c) | Q(categoria_2=c) | Q(categoria_3=c)
        qs = qs.filter(cat_q)
 
    filter_active = bool(q.strip() or date_from or date_to or cats or include_public)
 
    # ---- pagination ----
    paginator   = Paginator(qs, NEWS_PER_PAGE)
    page_number = request.GET.get("page", 1)
    page_obj    = paginator.get_page(page_number)
 
    context = {
        "news_list":            page_obj,
        "page_obj":             page_obj,
        "page_type":            "subscriber",
        "page_title":           "Notícias Exclusivas",
        "page_subtitle":        "Conteúdo exclusivo para subscritores",
        # filter state
        "filter_q":             q,
        "filter_date_from":     date_from,
        "filter_date_to":       date_to,
        "filter_cats":          cats,
        "filter_include_public": include_public,
        "filter_active":        filter_active,
        "categories":           CATEGORIES,
    }
    return render(request, "com_soc/subscriber.html", context)

@authenticated_user
def sub_ad(request):
    if request.user.role == 'Subscritor':
        return redirect('subscriber')
    context = {
        'page_type': 'sub_ad',
        'page_title': 'Subscrição',
    }
    return render(request, "com_soc/sub_ad.html", context)

@authenticated_user
def notifications(request):
    notifications_list = Notificacao.objects.filter(
        utilizador=request.user,
        estado=Notificacao.Estado.NORMAL
    ).order_by("-timestamp")

    context = {
        "notifications_list": notifications_list,
        'page_type': 'notifications',
        'page_title': 'Notificacoes',
    }
    return render(request, "com_soc/notification.html", context)

@authenticated_user
def definicoes(request):

    config = get_object_or_404(ModerationConfig, name="default")

    context = {
        'page_type': 'definicoes',
        'page_title': 'Definições',
        "moderation_config": config
    }
    return render(request, "com_soc/definicoes.html", context)
 

# -----------------------------------------------------------------------
# Notifications actions
# -----------------------------------------------------------------------
 
@require_POST
@authenticated_user
def delete_notification(request, id):
    notif = get_object_or_404(Notificacao, id=id, utilizador=request.user)
    notif.estado = Notificacao.Estado.APAGADA
    notif.save()
    return JsonResponse({'success': True})
 
 
@require_POST
@authenticated_user
def delete_all_notifications(request):
    Notificacao.objects.filter(
        utilizador=request.user,
        estado=Notificacao.Estado.NORMAL
    ).update(estado=Notificacao.Estado.APAGADA)
    return JsonResponse({'success': True})
 
 
@require_POST
@authenticated_user
def mark_notifications_read(request):
    Notificacao.objects.filter(
        utilizador=request.user,
        estado=Notificacao.Estado.NORMAL,
        read=Notificacao.Read.POR_VER
    ).update(read=Notificacao.Read.VISTA)
    return JsonResponse({'success': True})

# ---------------------------------------------------------------------------
# Editor
# ---------------------------------------------------------------------------

@authenticated_user
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

    for news in pendentes:
        news.ai_json = json.dumps(news.ai_evaluation) if news.ai_evaluation else ''
    for news in publicadas:
        news.ai_json = json.dumps(news.ai_evaluation) if news.ai_evaluation else ''

    context = {
        'pendentes': pendentes,
        'publicadas': publicadas,
        'page_type': 'editor',
        'page_title': 'Editor',
    }
    return render(request, "com_soc/editor.html", context)

@require_POST
@authenticated_user
@editor_required
def aceitar_noticia(request, id):
    noticia = get_object_or_404(Noticia, id=id)
    noticia.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
    noticia.data_publicacao = timezone.now().date()
    noticia.editor_aprovador = request.user
    noticia.save()
    message = f"A notícia '{noticia.titulo}' foi aceite e publicada."
    create_notification(noticia.autor,message)
    return JsonResponse({'success': True})

@require_POST
@authenticated_user
@editor_required
def eliminar_noticia(request, id):
    noticia = get_object_or_404(Noticia, id=id)
    noticia.delete()
    message = f"A notícia '{noticia.titulo}' foi rejeitada."
    create_notification(noticia.autor,message)
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# News detail & comments
# ---------------------------------------------------------------------------

@authenticated_user
def noticia_detail(request, noticia_id):
    noticia = get_object_or_404(Noticia, pk=noticia_id)

    user_is_editor = (request.user.is_staff or request.user.is_superuser)
    user_is_subscriber = (request.user.role == 'Subscritor' or user_is_editor)

    if noticia.acesso == Noticia.Acesso.PREMIUM and not user_is_subscriber:
        return redirect('sub_ad')

    if noticia.estado_publicacao == Noticia.EstadoPublicacao.PENDENTE and not user_is_editor:
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
@authenticated_user
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
            "avatar_url": comment.utilizador.profile_picture.url if comment.utilizador.profile_picture else None,
        }
    })


# ---------------------------------------------------------------------------
# Create & edit news
# ---------------------------------------------------------------------------

@require_POST
@authenticated_user
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
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
        noticia_obj.data_publicacao = timezone.now().date()
        noticia_obj.editor_aprovador = request.user
        noticia_obj.save()
    else:
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PRE_AI
        noticia_obj.origem_noticia = Noticia.OrigemNoticia.NOTICIAS_DO_POVO
        noticia_obj.acesso = Noticia.Acesso.PUBLICO
        noticia_obj.save()

        evaluate_noticia_task.delay(noticia_obj.id)

    for imagem in request.FILES.getlist("imagens"):
        ImagemNoticia.objects.create(noticia=noticia_obj, imagem=imagem)

    return JsonResponse({"success": True})

@authenticated_user
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

@require_POST
@authenticated_user
@editor_required
def editar_noticia(request, id):
    noticia = get_object_or_404(Noticia, pk=id)
    form = NoticiaForm(request.POST, instance=noticia, is_staff=True)
    if not form.is_valid():
        return JsonResponse({'success': False, 'error': form.errors}, status=400)
    form.save()
    return JsonResponse({'success': True})


# -----------------------------------------------------------------------
# Account views — add to views.py
# -----------------------------------------------------------------------
 
@authenticated_user
def account(request):
    active_sub = (
        request.user.subscricoes
        .filter(
            estado__in=['Ativa', 'Cancelada'],
            data_fim__gte=timezone.now().date()
        )
        .order_by('-data_fim')
        .first()
    )
    days_member = (timezone.now().date() - request.user.date_joined.date()).days

    context = {
        'page_type': 'account',
        'page_title': 'Minha Conta',
        'active_sub': active_sub,
        'days_member': days_member,
        'categoria_choices': Noticia.Categoria.choices,
    }
    return render(request, 'com_soc/account.html', context)
 
@require_POST
@authenticated_user
def update_avatar(request):
    picture = request.FILES.get('profile_picture')
 
    if not picture:
        return JsonResponse({'success': False, 'error': 'Nenhuma imagem recebida.'}, status=400)
 
    allowed_types = ('image/jpeg', 'image/png', 'image/gif', 'image/webp')
    if picture.content_type not in allowed_types:
        return JsonResponse({'success': False, 'error': 'Tipo de ficheiro não suportado.'}, status=400)
 
    if picture.size > 5 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': 'A imagem não pode exceder 5 MB.'}, status=400)
 
    user = request.user
    if user.profile_picture:
        try:
            user.profile_picture.delete(save=False)
        except Exception:
            pass
 
    user.profile_picture = picture
    user.save(update_fields=['profile_picture'])
 
    return JsonResponse({'success': True, 'url': user.profile_picture.url})
 
 
@require_POST
@authenticated_user
def update_username(request):
    new_username = request.POST.get('username', '').strip()
 
    if not new_username:
        return JsonResponse({'success': False, 'error': 'O nome não pode estar vazio.'}, status=400)
 
    if len(new_username) < 3:
        return JsonResponse({'success': False, 'error': 'Mínimo 3 caracteres.'}, status=400)
 
    validator = UnicodeUsernameValidator()
    try:
        validator(new_username)
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': e.messages[0]}, status=400)
 
    if (
        Utilizador.objects
        .filter(username__iexact=new_username)
        .exclude(pk=request.user.pk)
        .exists()
    ):
        return JsonResponse({'success': False, 'error': 'Este nome de utilizador já está em uso.'}, status=400)
 
    request.user.username = new_username
    request.user.save(update_fields=['username'])
 
    return JsonResponse({'success': True})
 
 
@require_POST
@authenticated_user
def change_password(request):
    current_pw = request.POST.get('current_password', '')
    new_pw = request.POST.get('new_password', '')
 
    if not request.user.check_password(current_pw):
        return JsonResponse({'success': False, 'error': 'A palavra-passe atual está incorreta.'}, status=400)
 
    if len(new_pw) < 8:
        return JsonResponse({'success': False, 'error': 'A nova palavra-passe deve ter pelo menos 8 caracteres.'}, status=400)
 
    if not any(c.isupper() for c in new_pw):
        return JsonResponse({'success': False, 'error': 'A nova palavra-passe deve conter pelo menos uma letra maiúscula.'}, status=400)
 
    if not any(c.isdigit() for c in new_pw):
        return JsonResponse({'success': False, 'error': 'A nova palavra-passe deve conter pelo menos um número.'}, status=400)
 
    request.user.set_password(new_pw)
    request.user.save()
    update_session_auth_hash(request, request.user)
 
    return JsonResponse({'success': True})

# -----------------------------------------------------------------------
# Settings views
# -----------------------------------------------------------------------
 
@require_POST
@authenticated_user
@editor_required
def save_config(request):

    data = json.loads(request.body)

    config = get_object_or_404(ModerationConfig, name="default")

    config.ideal_threshold = int(data["ideal_threshold"])
    config.low_threshold = int(data["low_threshold"])
    config.medium_threshold = int(data["medium_threshold"])
    config.high_threshold = int(data["high_threshold"])

    config.save()

    return JsonResponse({"success": True})
