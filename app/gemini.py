import json
import re
import asyncio
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FALLBACK_MODEL, GEMINI_FALLBACK_MODEL2

_client = genai.Client(api_key=GEMINI_API_KEY)

_RETRIES = 2


async def _generate_with_retry(contents, config) -> str:
    """
    Call Gemini with automatic fallback across 3 models on 503 overload,
    quota errors, or region restrictions.
    Order: gemini-3.1-flash-lite-preview → gemini-2.5-flash → gemini-2.5-flash-lite
    """
    models_to_try = [GEMINI_MODEL, GEMINI_FALLBACK_MODEL, GEMINI_FALLBACK_MODEL2]

    for model in models_to_try:
        for attempt in range(_RETRIES):
            try:
                response = _client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response.text
            except Exception as e:
                err = str(e)
                is_retryable = (
                    "503" in err or
                    "UNAVAILABLE" in err or
                    "overload" in err.lower() or
                    "429" in err or
                    "RESOURCE_EXHAUSTED" in err or
                    "FAILEDPRECONDITION" in err or   # region restriction — try next model
                    ("400" in err and "location" in err.lower())
                )
                if is_retryable:
                    if attempt < _RETRIES - 1:
                        await asyncio.sleep(2)
                    else:
                        break   # try next model
                else:
                    raise       # real error, don't retry

    raise Exception("All Gemini models are currently unavailable. Please try again in a moment.")


_PARSE_PROMPT = """\
You are a spending log parser for a Malaysian user. Extract spending info from the message.
Return ONLY valid JSON — no markdown, no extra text, no explanation.

JSON keys:
- is_spending : boolean
- intent      : "log" | "summary_today" | "summary_week" | "summary_month" | "advice" | "help" | "unknown"
- amount      : float or null  (MYR amount, digits only)
- category    : one of [Food, Drinks, Groceries, Clothing, Transport, Entertainment, Health, Bills, Other] or null
- place       : string or null (store/restaurant name; "Unknown" if not mentioned)
- note        : string or null (max 6 words describing the spend)

Intent rules:
- "log"            → user is recording a new expense
- "summary_today"  → user asks about today's spending
- "summary_week"   → user asks about this week's spending
- "summary_month"  → user asks about this month's spending
- "advice"         → user asks ANY financial question, wants analysis, projections,
                     savings tips, budget advice, or asks "can i afford", "how much should i save",
                     "my salary is", "am i overspending", "what's my average", etc.
- "help"           → user asks what the bot can do
- "unknown"        → anything else

Examples:
"rm25 lunch mcdonalds"                    -> {"is_spending":true,"intent":"log","amount":25.0,"category":"Food","place":"McDonald's","note":"lunch at McDonald's"}
"grab rm12.50 to klcc"                   -> {"is_spending":true,"intent":"log","amount":12.5,"category":"Transport","place":"Grab","note":"ride to KLCC"}
"how much did i spend today"             -> {"is_spending":false,"intent":"summary_today","amount":null,"category":null,"place":null,"note":null}
"summary this week"                      -> {"is_spending":false,"intent":"summary_week","amount":null,"category":null,"note":null}
"summary this month"                     -> {"is_spending":false,"intent":"summary_month","amount":null,"category":null,"place":null,"note":null}
"how much did i spend this month"        -> {"is_spending":false,"intent":"summary_month","amount":null,"category":null,"place":null,"note":null}
"spending this month"                    -> {"is_spending":false,"intent":"summary_month","amount":null,"category":null,"place":null,"note":null}
"how much should i save daily"           -> {"is_spending":false,"intent":"advice","amount":null,"category":null,"place":null,"note":null}
"my salary is rm4000, can i afford rent" -> {"is_spending":false,"intent":"advice","amount":4000.0,"category":null,"place":null,"note":null}
"am i overspending on food"              -> {"is_spending":false,"intent":"advice","amount":null,"category":"Food","place":null,"note":null}
"analyse my spending habits"             -> {"is_spending":false,"intent":"advice","amount":null,"category":null,"place":null,"note":null}
"if i earn rm5000 how much is left"      -> {"is_spending":false,"intent":"advice","amount":5000.0,"category":null,"place":null,"note":null}
"help"                                   -> {"is_spending":false,"intent":"help","amount":null,"category":null,"place":null,"note":null}
"""


async def parse_message(text: str) -> dict:
    """Send user text to Gemini and return a parsed spending dict."""
    raw = await _generate_with_retry(
        contents=_PARSE_PROMPT + f'\n\nMessage: "{text}"',
        config=types.GenerateContentConfig(
            max_output_tokens=256,
            temperature=0.1,
        ),
    )
    raw = re.sub(r"```json|```", "", raw).strip()
    return json.loads(raw)
