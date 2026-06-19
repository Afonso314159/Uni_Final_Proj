from celery import shared_task
from datetime import date, timedelta
from .models import Subscricao
from .stripe_emails import send_renewal_warning_email
from .utils import create_notification

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