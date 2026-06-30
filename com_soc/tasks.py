from celery import shared_task
from datetime import date, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Subscricao, Noticia, ModerationConfig
from .stripe_emails import send_renewal_warning_email
from .utils import create_notification, AI_score

@shared_task
def enviar_avisos_renovacao():
    target_date = date.today() + timedelta(days=3)
    subscricoes = Subscricao.objects.filter(
        estado=Subscricao.Estado.ATIVA,
        data_fim=target_date,
    ).select_related('utilizador')

    count = 0
    for sub in subscricoes:
        user = sub.utilizador
        try:
            send_renewal_warning_email(user, sub)
            create_notification(
                user,
                f'A tua subscrição {sub.get_plano_display()} renova em 3 dias ({sub.data_fim}). Valor: {sub.preco}€'
            )
            count += 1
        except Exception as e:
            print(f'Erro ao notificar {user.username}: {e}')
    return f'{count} aviso(s) enviado(s).'

@shared_task
def evaluate_noticia_task(noticia_id):
    try:
        noticia_obj = Noticia.objects.get(id=noticia_id)
    except Noticia.DoesNotExist:
        print(f"evaluate_noticia_task: Noticia {noticia_id} não encontrada.")
        return

    config = get_object_or_404(ModerationConfig, name="default")
    evaluation = AI_score(noticia_obj, config)
    noticia_obj.ai_evaluation = evaluation
    risk_level = evaluation.get('risk_level', 'medium')

    if risk_level == 'trash':
        message = f"A notícia '{noticia_obj.titulo}' foi rejeitada."
        create_notification(noticia_obj.autor, message)
        noticia_obj.delete()
        return

    elif risk_level == 'ideal':
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PUBLICADA
        noticia_obj.data_publicacao = timezone.now().date()
        message = f"A notícia '{noticia_obj.titulo}' foi aceite e publicada."
        create_notification(noticia_obj.autor, message)

    else:
        noticia_obj.estado_publicacao = Noticia.EstadoPublicacao.PENDENTE
        message = f"A notícia '{noticia_obj.titulo}' esta pendente a espera de revisao."
        create_notification(noticia_obj.autor, message)

    noticia_obj.save()
