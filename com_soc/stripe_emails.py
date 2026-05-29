# com_soc/stripe_emails.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_subscription_active_email(user, subscricao):
    subject = 'Subscrição ativada — ComSoc'
    html_message = render_to_string('com_soc/emails/subscricao_ativa.html', {
        'user':       user,
        'subscricao': subscricao,
    })
    plain_message = (
        f"Olá {user.username},\n\n"
        f"A tua subscrição {subscricao.get_plano_display()} foi ativada com sucesso.\n"
        f"Válida até: {subscricao.data_fim}\n\n"
        "Obrigado por subscreveres!"
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_subscription_cancelled_email(user, subscricao):
    subject = 'Subscrição cancelada — ComSoc'
    html_message = render_to_string('com_soc/emails/subscricao_cancelada.html', {
        'user':       user,
        'subscricao': subscricao,
    })
    plain_message = (
        f"Olá {user.username},\n\n"
        "A tua subscrição foi cancelada.\n"
        "Esperamos ver-te de volta em breve!"
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_payment_failed_email(user, subscricao):
    subject = 'Problema com o teu pagamento — ComSoc'
    html_message = render_to_string('com_soc/emails/pagamento_falhou.html', {
        'user':       user,
        'subscricao': subscricao,
    })
    plain_message = (
        f"Olá {user.username},\n\n"
        "Não foi possível processar o pagamento da tua subscrição.\n"
        "A tua subscrição foi suspensa. Atualiza os teus dados de pagamento para continuar a ter acesso."
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )


def send_renewal_warning_email(user, subscricao):
    subject = 'A tua subscrição renova em 3 dias — ComSoc'
    html_message = render_to_string('com_soc/emails/aviso_renovacao.html', {
        'user':       user,
        'subscricao': subscricao,
    })
    plain_message = (
        f"Olá {user.username},\n\n"
        f"A tua subscrição {subscricao.get_plano_display()} renova automaticamente em 3 dias "
        f"({subscricao.data_fim}).\n"
        f"Valor a cobrar: {subscricao.preco}€\n\n"
        "Se não quiseres renovar, cancela antes dessa data."
    )
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=True,
    )