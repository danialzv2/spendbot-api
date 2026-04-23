import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sheets import init_sheet, insert_spending, query_summary, get_financial_context
from gemini import parse_message
from advisor import get_advice
from telegram import send_message, format_log_reply, format_summary, HELP_TEXT

# ── App lifecycle ─────────────────────────────────────────────────────────────
sheet = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sheet
    sheet = init_sheet()
    yield

app = FastAPI(lifespan=lifespan)

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
async def health():
    return {"status": "SpendBot is running 🚀"}

# ── Webhook ───────────────────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    message = data.get("message") or data.get("edited_message")
    if not message:
        return JSONResponse({"ok": True})

    chat_id = message["chat"]["id"]
    text    = message.get("text", "").strip()
    if not text:
        return JSONResponse({"ok": True})

    try:
        parsed = await parse_message(text)
        intent = parsed.get("intent", "unknown")

        if parsed.get("is_spending") and intent == "log":
            timestamp = insert_spending(
                sheet,
                chat_id  = chat_id,
                amount   = parsed["amount"],
                category = parsed["category"],
                place    = parsed.get("place") or "Unknown",
                note     = parsed.get("note") or "",
            )
            reply = format_log_reply(parsed, timestamp)

        elif intent == "summary_today":
            reply = format_summary(query_summary(sheet, chat_id, "today"))

        elif intent == "summary_week":
            reply = format_summary(query_summary(sheet, chat_id, "week"))

        elif intent == "summary_month":
            reply = format_summary(query_summary(sheet, chat_id, "month"))

        elif intent == "advice":
            # Pull rich spending context, then ask Gemini for advice
            await send_message(chat_id, "🤔 _Analysing your spending data..._")
            try:
                context = get_financial_context(sheet, chat_id)
                reply   = await get_advice(question=text, context=context)
            except Exception as e:
                reply = f"⚠️ Couldn't generate advice: {str(e)}"

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