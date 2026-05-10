import httpx
from config import TELEGRAM_API, CAT_EMOJI

# ── Send ──────────────────────────────────────────────────────────────────────
async def send_message(chat_id: int, text: str) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )

# ── Formatters ────────────────────────────────────────────────────────────────
def format_log_reply(parsed: dict, timestamp: str) -> str:
    emoji = CAT_EMOJI.get(parsed["category"], "📦")
    return (
        f"✅ *Logged!* _{timestamp}_\n\n"
        f"{emoji} *{parsed['category']}* — RM {parsed['amount']:.2f}\n"
        f"📍 {parsed.get('place') or 'Unknown'}\n"
        f"📝 {parsed.get('note') or '-'}"
    )


def format_receipt_reply(parsed: dict, timestamp: str) -> str:
    emoji      = CAT_EMOJI.get(parsed["category"], "📦")
    confidence = parsed.get("confidence", "high")
    conf_note  = "" if confidence == "high" else f"\n⚠️ _Confidence: {confidence} — please verify amount_"
    items      = parsed.get("items", [])
    items_str  = "\n" + "\n".join(f"  · {i}" for i in items) if items else ""
    return (
        f"🧾 *Receipt logged!* _{timestamp}_\n\n"
        f"{emoji} *{parsed['category']}* — RM {parsed['amount']:.2f}\n"
        f"📍 {parsed.get('place') or 'Unknown'}\n"
        f"📝 {parsed.get('note') or '-'}"
        f"{items_str}"
        f"{conf_note}"
    )


def format_summary(data: dict) -> str:
    period_label = {
        "today": "Today",
        "week":  "Last 7 days",
        "month": "This Month",
    }
    label = period_label.get(data["period"], "Period")
    if data["total"] == 0:
        return f"📭 No spending recorded for *{label.lower()}* yet."
    lines = [f"📊 *{label} — RM {data['total']:.2f}*\n"]
    for cat, amt in data["breakdown"].items():
        emoji = CAT_EMOJI.get(cat, "📦")
        pct   = (amt / data["total"]) * 100
        lines.append(f"{emoji} {cat}: RM {amt:.2f} ({pct:.0f}%)")
    return "\n".join(lines)


HELP_TEXT = """\
💸 *SpendBot Commands*

*Log spending — just type naturally:*
• `rm25 lunch mcdonalds`
• `grab rm12.50 to klcc`
• `rm8 nasi lemak`
• `rm129 shoes parkson`
• `netflix rm17`

*Scan a receipt 🧾*
Just send a photo of your receipt — SpendBot will read it automatically!

*Check your spending:*
• `summary today`
• `summary this week`
• `summary this month`

*Ask for financial advice:*
• `how much should i save daily?`
• `my salary is rm4000, am i overspending?`
• `can i afford rm800 rent?`
• `analyse my spending habits`
• `which category should i cut down?`
• `how much will i spend this month?`

*Other:*
• `help` — show this message

_All times are Malaysia Time (MYT, UTC+8)_
"""