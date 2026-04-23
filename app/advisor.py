import json
from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(api_key=GEMINI_API_KEY)

_ADVISOR_SYSTEM = """\
You are SpendBot's personal finance advisor for a Malaysian user.
You have access to the user's real spending data (provided below) and must give
specific, actionable, numbers-first advice in a friendly but direct tone.

Rules:
- Always use RM (Malaysian Ringgit)
- Be concise — max 5 short paragraphs, use bullet points where helpful
- Reference the user's ACTUAL numbers from the context, don't be generic
- If salary/budget is mentioned in the question, use it in your calculation
- If data is insufficient for a question, say so honestly
- Use Telegram Markdown: *bold*, _italic_, `code` for numbers
- Never use headers with #, use *bold* instead
- End with one short actionable tip

Spending context (Malaysia Time, MYT):
{context}

User question: {question}
"""


async def get_advice(question: str, context: dict) -> str:
    """Get AI financial advice grounded in the user's real spending data."""
    if not context:
        return (
            "⚠️ No spending data found yet. "
            "Log some transactions first so I can give you personalised advice!\n\n"
            "Try: `rm25 lunch mcdonalds`"
        )

    context_str = json.dumps(context, indent=2)
    prompt = _ADVISOR_SYSTEM.format(context=context_str, question=question)

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()