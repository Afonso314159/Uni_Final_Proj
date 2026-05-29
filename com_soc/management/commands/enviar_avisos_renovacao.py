# com_soc/management/commands/enviar_avisos_renovacao.py

from django.core.management.base import BaseCommand
from datetime import date, timedelta
from com_soc.models import Subscricao
from com_soc.stripe_emails import send_renewal_warning_email
from com_soc.utils import create_notification


class Command(BaseCommand):
    help = 'Envia avisos de renovação para subscritores cujo plano renova em 3 dias'

    def handle(self, *args, **options):
        target_date  = date.today() + timedelta(days=3)
        subscricoes  = Subscricao.objects.filter(
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
                    f'A tua subscrição {sub.get_plano_display()} renova automaticamente em 3 dias ({sub.data_fim}). Valor: {sub.preco}€'
                )
                count += 1
            except Exception as e:
                self.stderr.write(f'Erro ao notificar {user.username}: {e}')

        self.stdout.write(self.style.SUCCESS(f'{count} aviso(s) de renovação enviado(s).'))