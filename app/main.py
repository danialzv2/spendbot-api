from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx
import os
import json
import re
from datetime import datetime, timedelta
from google import genai
import gspread
from google.oauth2.service_account import Credentials
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GSHEET_NAME    = os.environ.get("GSHEET_NAME", "SpendBot")
GSHEET_CREDS   = os.environ["GSHEET_CREDS"]
TELEGRAM_API   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ── Gemini init (new SDK) ─────────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GEMINI_API_KEY)
GEMINI_MODEL  = "gemini-3.1-flash-lite-preview"

# ── Google Sheets init ────────────────────────────────────────────────────────
def init_sheet():
    creds_dict = json.loads(GSHEET_CREDS)
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(GSHEET_NAME).sheet1
    if not sheet.row_values(1):
        sheet.append_row(["timestamp", "chat_id", "amount", "category", "place", "note"])
    return sheet

# ── Sheet helpers ─────────────────────────────────────────────────────────────
def insert_spending(sheet, chat_id: int, amount: float, category: str, place: str, note: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row(
        [now, str(chat_id), amount, category, place, note],
        value_input_option="USER_ENTERED"
    )

def query_summary(sheet, chat_id: int, period: str = "month") -> dict:
    records = sheet.get_all_records()
    now = datetime.now()
    if period == "today":
        cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        cutoff = now - timedelta(days=7)
    else:
        cutoff = now - timedelta(days=30)

    breakdown = {}
    total = 0.0
    for row in records:
        if str(row.get("chat_id")) != str(chat_id):
            continue
        try:
            ts = datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if ts < cutoff:
            continue
        cat = row.get("category", "Other")
        amt = float(row.get("amount", 0))
        breakdown[cat] = breakdown.get(cat, 0.0) + amt
        total += amt

    breakdown = dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))
    return {"total": total, "breakdown": breakdown, "period": period}

# ── Gemini parser ─────────────────────────────────────────────────────────────
PARSE_PROMPT = """\
You are a spending log parser for a Malaysian user. Extract spending info from the message.
Return ONLY valid JSON, no markdown, no extra text.

JSON keys:
- is_spending: boolean
- intent: "log" | "summary_today" | "summary_week" | "summary_month" | "help" | "unknown"
- amount: float or null (MYR amount)
- category: one of [Food, Transport, Shopping, Entertainment, Health, Bills, Education, Other] or null
- place: string or null (shop/restaurant name, "Unknown" if not mentioned)
- note: string or null (max 6 words describing the spend)

Examples:
"rm25 lunch mcdonalds" -> {"is_spending":true,"intent":"log","amount":25.0,"category":"Food","place":"McDonald's","note":"lunch at McDonald's"}
"grab rm12.50 to klcc" -> {"is_spending":true,"intent":"log","amount":12.5,"category":"Transport","place":"Grab","note":"ride to KLCC"}
"how much did i spend today" -> {"is_spending":false,"intent":"summary_today","amount":null,"category":null,"place":null,"note":null}
"summary this week" -> {"is_spending":false,"intent":"summary_week","amount":null,"category":null,"place":null,"note":null}
"help" -> {"is_spending":false,"intent":"help","amount":null,"category":null,"place":null,"note":null}
"""

async def parse_message(text: str) -> dict:
    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=PARSE_PROMPT + f'\n\nMessage: "{text}"',
    )
    raw = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(raw)

# ── Telegram helpers ──────────────────────────────────────────────────────────
CAT_EMOJI = {
    "Food": "🍜", "Transport": "🚗", "Shopping": "🛍️",
    "Entertainment": "🎮", "Health": "💊", "Bills": "📄",
    "Education": "📚", "Other": "📦",
}

async def send_message(chat_id: int, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })

def format_summary(data: dict) -> str:
    period_label = {"today": "Today", "week": "Last 7 days", "month": "Last 30 days"}
    label = period_label.get(data["period"], "Period")
    if data["total"] == 0:
        return f"📭 No spending recorded for *{label.lower()}* yet."
    lines = [f"📊 *{label} — RM {data['total']:.2f}*\n"]
    for cat, amt in data["breakdown"].items():
        emoji = CAT_EMOJI.get(cat, "📦")
        pct = (amt / data["total"]) * 100
        lines.append(f"{emoji} {cat}: RM {amt:.2f} ({pct:.0f}%)")
    return "\n".join(lines)

HELP_TEXT = """\
💸 *SpendBot Commands*

*Log spending (just type naturally):*
• `rm25 lunch mcdonalds`
• `grab rm12.50 to klcc`
• `rm8 nasi lemak`
• `rm129 shoes parkson`
• `netflix rm17`

*Check your spending:*
• `summary today`
• `summary this week`
• `summary this month`

*Other:*
• `help` — show this message
"""

# ── App lifecycle ─────────────────────────────────────────────────────────────
sheet = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sheet
    sheet = init_sheet()
    yield

app = FastAPI(lifespan=lifespan)

# ── Webhook endpoint ──────────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    message = data.get("message") or data.get("edited_message")
    if not message:
        return JSONResponse({"ok": True})

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": True})

    try:
        parsed = await parse_message(text)
        intent = parsed.get("intent", "unknown")

        if parsed.get("is_spending") and intent == "log":
            insert_spending(sheet, chat_id=chat_id, amount=parsed["amount"],
                            category=parsed["category"], place=parsed.get("place") or "Unknown",
                            note=parsed.get("note") or "")
            emoji = CAT_EMOJI.get(parsed["category"], "📦")
            reply = (f"✅ *Logged!*\n\n"
                     f"{emoji} *{parsed['category']}* — RM {parsed['amount']:.2f}\n"
                     f"📍 {parsed.get('place') or 'Unknown'}\n"
                     f"📝 {parsed.get('note') or '-'}")

        elif intent == "summary_today":
            reply = format_summary(query_summary(sheet, chat_id, "today"))
        elif intent == "summary_week":
            reply = format_summary(query_summary(sheet, chat_id, "week"))
        elif intent == "summary_month":
            reply = format_summary(query_summary(sheet, chat_id, "month"))
        elif intent == "help":
            reply = HELP_TEXT
        else:
            reply = "🤔 I didn't catch that. Type `help` to see what I can do."

    except json.JSONDecodeError:
        reply = "⚠️ Couldn't parse that. Try: `rm25 food mcdonalds`"
    except Exception as e:
        reply = f"⚠️ Something went wrong: {str(e)}"

    await send_message(chat_id, reply)
    return JSONResponse({"ok": True})

@app.get("/")
async def health():
    return {"status": "SpendBot is running 🚀"}