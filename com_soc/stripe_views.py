# com_soc/stripe_views.py

import stripe
import json
from datetime import date

from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from com_soc.stripe_emails import send_subscription_active_email,send_subscription_cancelled_email, send_payment_failed_email
from .utils import create_notification

from .models import Subscricao, Utilizador

stripe.api_key = settings.STRIPE_SECRET_KEY

PLANO_PRICE_MAP = {
    'mensal': settings.STRIPE_PRICE_MENSAL,
    'anual':  settings.STRIPE_PRICE_ANUAL,
}

PLANO_PRECO = {
    'mensal': 0.99,
    'anual':  9.99,
}


# ─── 1. Create Checkout Session ───────────────────────────────────────────────

@login_required
@require_POST
def criar_checkout_session(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Pedido inválido.'}, status=400)

    plano = data.get('plano')

    if plano not in PLANO_PRICE_MAP:
        return JsonResponse({'error': 'Plano inválido.'}, status=400)

    # Check for already active subscription
    sub_existente = Subscricao.objects.filter(
        utilizador=request.user,
        estado__in=[Subscricao.Estado.ATIVA, Subscricao.Estado.CANCELADA],
        data_fim__gte=date.today()
    ).exists()

    if sub_existente:
        return JsonResponse({'error': 'Já tens uma subscrição ativa.'}, status=400)
    
    # Reuse Stripe customer if user has subscribed before
    sub_anterior = Subscricao.objects.filter(
        utilizador=request.user,
        stripe_customer_id__isnull=False
    ).first()

    customer_id = sub_anterior.stripe_customer_id if sub_anterior else None

    try:
        checkout_kwargs = {
            'payment_method_types': ['card'],
            'line_items': [{'price': PLANO_PRICE_MAP[plano], 'quantity': 1}],
            'mode': 'subscription',
            'success_url': request.build_absolute_uri('/com_soc/subscricao/sucesso/') + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url':  request.build_absolute_uri('/com_soc/subscricao/cancelado/'),
            'metadata': {
                'utilizador_id': str(request.user.id),
                'plano': plano,
            },
        }

        if customer_id:
            checkout_kwargs['customer'] = customer_id
        else:
            checkout_kwargs['customer_email'] = request.user.email

        session = stripe.checkout.Session.create(**checkout_kwargs)

        return JsonResponse({'checkout_url': session.url})

    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── 2. Success & Cancel Pages ────────────────────────────────────────────────

def checkout_sucesso(request):
    return render(request, 'com_soc/checkout_sucesso.html')


def checkout_cancelado(request):
    return render(request, 'com_soc/checkout_cancelado.html')


# ─── 3. Webhook Handler ───────────────────────────────────────────────────────

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload    = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)  # Invalid payload
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)  # Invalid signature

    event_type = event['type']
    obj        = event['data']['object']

    if event_type == 'checkout.session.completed':
        _handle_checkout_completed(obj)

    elif event_type == 'customer.subscription.updated':
        _handle_subscription_updated(obj)

    elif event_type == 'customer.subscription.deleted':
        _handle_subscription_deleted(obj)

    elif event_type == 'invoice.payment_failed':
        _handle_payment_failed(obj)

    return HttpResponse(status=200)


# ─── Webhook Helpers ──────────────────────────────────────────────────────────

def _handle_checkout_completed(session):
    try:
        metadata      = session['metadata']
        utilizador_id = metadata['utilizador_id']
        plano         = metadata['plano']
    except (KeyError, AttributeError, TypeError):
        return
 
    customer_id     = session['customer']
    subscription_id = session['subscription']
 
    if not subscription_id:
        return
 
    stripe_sub  = stripe.Subscription.retrieve(subscription_id)
    first_item  = stripe_sub['items']['data'][0]
    data_inicio = date.fromtimestamp(first_item['current_period_start'])
    data_fim    = date.fromtimestamp(first_item['current_period_end'])
 
    sub, _ = Subscricao.objects.update_or_create(
        stripe_subscription_id=subscription_id,
        defaults={
            'utilizador_id':      utilizador_id,
            'plano':              plano,
            'estado':             Subscricao.Estado.ATIVA,
            'data_inicio':        data_inicio,
            'data_fim':           data_fim,
            'stripe_customer_id': customer_id,
            'preco':              PLANO_PRECO.get(plano),
        }
    )
 
    user = get_object_or_404(Utilizador, id=utilizador_id)
    user.role = Utilizador.Role.SUBSCRITOR
    user.save()
 
    send_subscription_active_email(user, sub)
    create_notification(
        user,
        f'Subscrição {sub.get_plano_display()} ativada com sucesso! Válida até {sub.data_fim}.'
    )
 
 
def _handle_subscription_updated(subscription):
    status              = subscription['status']
    cancel_at_period_end = subscription.get('cancel_at_period_end', False)

    try:
        first_item = subscription['items']['data'][0]
        data_fim   = date.fromtimestamp(first_item['current_period_end'])
    except (KeyError, IndexError, TypeError):
        data_fim = None

    if cancel_at_period_end:
        estado = Subscricao.Estado.CANCELADA
    elif status == 'active':
        estado = Subscricao.Estado.ATIVA
    else:
        estado = Subscricao.Estado.EXPIRADA

    update_fields = {'estado': estado}
    if data_fim:
        update_fields['data_fim'] = data_fim

    Subscricao.objects.filter(
        stripe_subscription_id=subscription['id']
    ).update(**update_fields)

    try:
        sub  = Subscricao.objects.get(stripe_subscription_id=subscription['id'])
        user = sub.utilizador
        user.role = (
            Utilizador.Role.SUBSCRITOR
            if sub.tem_acesso
            else Utilizador.Role.REGISTADO
        )
        user.save()
    except Subscricao.DoesNotExist:
        pass
 
 
def _handle_subscription_deleted(subscription):
    Subscricao.objects.filter(
        stripe_subscription_id=subscription['id']
    ).update(estado=Subscricao.Estado.CANCELADA)
 
    try:
        sub  = Subscricao.objects.get(stripe_subscription_id=subscription['id'])
        user = sub.utilizador
        user.role = Utilizador.Role.REGISTADO 
        user.save()
 
        send_subscription_cancelled_email(user, sub)
        create_notification(
            user,
            'A tua subscrição foi cancelada. O acesso ao conteúdo exclusivo foi removido.'
        )
    except Subscricao.DoesNotExist:
        pass
 
 
def _handle_payment_failed(invoice):
    try:
        subscription_id = invoice['subscription']
    except (KeyError, AttributeError, TypeError):
        return
 
    if not subscription_id:
        return
 
    Subscricao.objects.filter(
        stripe_subscription_id=subscription_id
    ).update(estado=Subscricao.Estado.EXPIRADA)
 
    try:
        sub  = Subscricao.objects.get(stripe_subscription_id=subscription_id)
        user = sub.utilizador
        user.role = Utilizador.Role.REGISTADO
        user.save()
 
        send_payment_failed_email(user, sub)
        create_notification(
            user,
            'Não foi possível processar o pagamento da tua subscrição. O acesso foi suspenso.'
        )
    except Subscricao.DoesNotExist:
        pass
 

@login_required
@require_POST
def cancelar_subscricao(request):
    sub = Subscricao.objects.filter(
        utilizador=request.user,
        estado=Subscricao.Estado.ATIVA
    ).first()

    if not sub:
        return JsonResponse({'error': 'Não tens uma subscrição ativa.'}, status=400)

    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            cancel_at_period_end=True
        )

        sub.estado = Subscricao.Estado.CANCELADA  # ← add
        sub.save()  

        send_subscription_cancelled_email(request.user, sub)
        create_notification(
            request.user,
            f'Subscrição cancelada. A renovação automática foi desativada — o teu acesso continua ativo até {sub.data_fim}.'
        )

        return JsonResponse({'ok': True})
    except stripe.error.StripeError as e:
        return JsonResponse({'error': str(e)}, status=400)