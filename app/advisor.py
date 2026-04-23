import json
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

# ── Token budget ──────────────────────────────────────────────────────────────
_MAX_OUTPUT_TOKENS = 400   # ~300 words — enough for advice without being excessive

_ADVISOR_SYSTEM = """\
You are SpendBot's finance advisor for a Malaysian user. Be concise and direct.

Rules:
- Max 3 short paragraphs or bullet points. No fluff.
- Use RM. Reference the user's ACTUAL numbers.
- Use Telegram Markdown: *bold*, `numbers`. No # headers.
- If salary/budget given, calculate exactly. End with one tip.

Spending context:
{context}

Question: {question}
"""

# Keys to keep — drop verbose breakdowns to save input tokens
_CONTEXT_KEYS = [
    "spend_today", "spend_this_week", "spend_this_month", "spend_last_month",
    "avg_daily_this_month", "avg_daily_last_month", "avg_daily_last_30_days",
    "projected_month_spend", "days_left_in_month",
    "top_categories_this_month", "avg_transaction_amount", "total_transactions_30d",
]

def _trim_context(context: dict) -> dict:
    """Keep only the keys the advisor needs — reduces input tokens significantly."""
    trimmed = {k: context[k] for k in _CONTEXT_KEYS if k in context}
    # Limit top_categories to top 4 only
    if "top_categories_this_month" in trimmed:
        cats = trimmed["top_categories_this_month"]
        trimmed["top_categories_this_month"] = dict(list(cats.items())[:4])
    return trimmed


async def get_advice(question: str, context: dict) -> str:
    """Get AI financial advice grounded in the user's real spending data."""
    if not context:
        return (
            "⚠️ No spending data yet. "
            "Log some transactions first!\n\n"
            "Try: `rm25 lunch mcdonalds`"
        )

    trimmed     = _trim_context(context)
    context_str = json.dumps(trimmed, separators=(",", ":"))  # compact, no whitespace
    prompt      = _ADVISOR_SYSTEM.format(context=context_str, question=question)

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=_MAX_OUTPUT_TOKENS,
            temperature=0.4,   # lower = more focused, less rambling
        ),
    )
    return response.text.strip()