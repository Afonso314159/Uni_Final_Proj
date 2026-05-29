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
    ja_tem_sub_ativa = Subscricao.objects.filter(
        utilizador=request.user,
        estado=Subscricao.Estado.ATIVA
    ).exists()

    if ja_tem_sub_ativa:
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
    # StripeObject doesn't support .get() — use [] with try/except
    try:
        metadata      = session['metadata']
        utilizador_id = metadata['utilizador_id']
        plano         = metadata['plano']
    except (KeyError, AttributeError, TypeError):
        # Missing metadata — stripe trigger test events hit this, that's fine
        return

    customer_id     = session['customer']
    subscription_id = session['subscription']

    if not subscription_id:
        return

    stripe_sub  = stripe.Subscription.retrieve(subscription_id)
    first_item  = stripe_sub['items']['data'][0]
    data_inicio = date.fromtimestamp(first_item['current_period_start'])
    data_fim    = date.fromtimestamp(first_item['current_period_end'])

    Subscricao.objects.update_or_create(
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

def _handle_subscription_updated(subscription):
    status  = subscription['status']
    data_fim = date.fromtimestamp(subscription['current_period_end'])

    estado = (
        Subscricao.Estado.ATIVA
        if status == 'active'
        else Subscricao.Estado.EXPIRADA
    )

    Subscricao.objects.filter(
        stripe_subscription_id=subscription['id']
    ).update(estado=estado, data_fim=data_fim)


def _handle_subscription_deleted(subscription):
    Subscricao.objects.filter(
        stripe_subscription_id=subscription['id']
    ).update(estado=Subscricao.Estado.CANCELADA)


def _handle_payment_failed(invoice):
    try:
        subscription_id = invoice['subscription']
    except (KeyError, AttributeError, TypeError):
        return
    if subscription_id:
        Subscricao.objects.filter(
            stripe_subscription_id=subscription_id
        ).update(estado=Subscricao.Estado.EXPIRADA)