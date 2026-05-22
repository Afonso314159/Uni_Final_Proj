import json
import requests
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
import os

# ---------------------------------------------------------------------------
# AI Moderation
# ---------------------------------------------------------------------------

_AI_PROMPT = """You are an AI system specialized in detecting misinformation and abusive content in news articles.

Analyze the following news text and evaluate:
1) The likelihood of the content being false or misleading.
2) The presence of abusive, offensive, or harmful language.

Return ONLY a valid JSON object with the following fields:
- fake_score: integer from 0 to 100 (0 = fully credible, 100 = highly likely fake/misleading)
- abusive_score: integer from 0 to 100 (0 = no abusive content, 100 = highly abusive)
- risk_level: "ideal", "low", "medium", "high" or "trash"
  (ideal if both are 0; low if both below 20; medium if both below 40;
   high if both below 70; trash if either score is 70 or above)
- reasons: a short list (2-5 items) explaining key signals
- recommendation: a short sentence suggesting what to do

Rules:
- Be objective and concise.
- Do not include any text outside the JSON.
- Do not include explanations before or after the JSON.
- Ensure the JSON is valid and properly formatted.

News text to analyze:"""

_FALLBACK_EVALUATION = {
    "fake_score": 50,
    "abusive_score": 50,
    "risk_level": "medium",
    "reasons": ["AI evaluation failed — manual review required."],
    "recommendation": "Review manually due to an AI evaluation error.",
}


def AI_score(noticia):

    """
    Calls the Google Gemini API to evaluate a news article.
    Returns a dict with: fake_score, abusive_score, risk_level, reasons, recommendation.
    """
    
    AI_API_KEY = os.getenv('GEMINI_API_KEY')
    AI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={AI_API_KEY}"

    news_text = f"{noticia.titulo}\n\n{noticia.corpo_texto}"
    full_prompt = f"{_AI_PROMPT}\n\n«{news_text}»\n\nRESPOSTA:"

    # 2. Estrutura do payload exigida pela API da Google
    payload = {
        "contents": [{
            "parts": [{"text": full_prompt}]
        }],
        # Isto força o Gemini a responder estritamente em formato JSON válido
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            AI_API_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        # 3. Parsing da resposta específica do Gemini
        response_json = response.json()
        
        # O texto gerado pelo Gemini fica sempre escondido dentro desta estrutura:
        raw_text = response_json['candidates'][0]['content']['parts'][0]['text']
        
        # Limpa eventuais marcações de markdown adicionais
        raw_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()
        
        return json.loads(raw_text)

    except Exception as e:
        print(f"Erro na moderação IA: {e}")
        return _FALLBACK_EVALUATION


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generates a one-time token tied to the user's pk, email, and active state.
    The token becomes invalid as soon as is_active becomes True,
    so the link cannot be reused after the first click.
    """
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_active}{user.email}"


email_verification_token = EmailVerificationTokenGenerator()


def send_verification_email(request, user):
    """
    Sends an HTML verification email to the user with a signed one-time link.
    Raises on delivery failure (fail_silently=False) — caller should catch this.
    """
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = request.build_absolute_uri(
        reverse('verify_email', kwargs={'uidb64': uid, 'token': token})
    )

    subject = 'Verifica o teu email — ComSoc'
    html_message = render_to_string('registration/verification_email.html', {
        'user': user,
        'link': link,
    })
    plain_message = (
        f"Olá {user.username},\n\n"
        f"Clica no link abaixo para verificares o teu email:\n{link}\n\n"
        "Se não criaste uma conta, ignora este email."
    )

    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )