import json
import requests

# ---------------------------------------------------------------------------
# AI Moderation Prompt
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
  (e.g., lack of sources, emotional language, insults, exaggeration)
- recommendation: a short sentence suggesting what to do
  (e.g., "verify with trusted sources", "flag for moderation")

Rules:
- Be objective and concise.
- Do not include any text outside the JSON.
- Do not include explanations before or after the JSON.
- Ensure the JSON is valid and properly formatted.

News text to analyze:"""

# ---------------------------------------------------------------------------
# Fallback evaluation used whenever the API call fails
# — sends the article to human review so nothing slips through silently
# ---------------------------------------------------------------------------
_FALLBACK_EVALUATION = {
    "fake_score": 50,
    "abusive_score": 50,
    "risk_level": "medium",
    "reasons": ["AI evaluation failed — manual review required."],
    "recommendation": "Review manually due to an AI evaluation error.",
}


def AI_score(noticia):
    """
    Calls the AI moderation API to evaluate a news article.

    Returns a dict with:
        fake_score      int  0-100
        abusive_score   int  0-100
        risk_level      str  "ideal" | "low" | "medium" | "high" | "trash"
        reasons         list[str]
        recommendation  str

    On any network or parsing error, returns _FALLBACK_EVALUATION so the
    article is never silently lost — it lands in the pending queue instead.

    TODO: replace the URL, key and response parsing below with your actual
    API credentials and response schema once the service is available.
    """

    # ------------------------------------------------------------------
    # TODO: move these to environment variables (e.g. via django-environ
    # or os.getenv) before going to production.
    # ------------------------------------------------------------------
    AI_API_URL = "https://your-ai-api-endpoint.com/v1/evaluate"
    AI_API_KEY = "your-api-key-here"

    news_text = f"{noticia.titulo}\n\n{noticia.corpo_texto}"
    full_prompt = f"{_AI_PROMPT}\n\n«{news_text}»\n\nRESPOSTA:"

    try:
        response = requests.post(
            AI_API_URL,
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            # TODO: adjust the request body to match your API's schema
            json={"prompt": full_prompt},
            timeout=30,
        )
        response.raise_for_status()

        # TODO: adjust the key below to match your API's response structure
        # e.g. response.json()["choices"][0]["message"]["content"]
        raw_text = response.json().get("content", "")

        # Strip accidental markdown fences if the model wraps in ```json
        raw_text = raw_text.strip().removeprefix("```json").removesuffix("```").strip()

        evaluation = json.loads(raw_text)
        return evaluation

    except Exception:
        return _FALLBACK_EVALUATION