"""
test_local.py — Test the bot locally without Telegram or a live webhook.

Usage:
    cd "AI Spending Tracker"
    python test_local.py
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv("app/.env")

from app.main import parse_message, insert_spending, query_summary, format_summary, init_sheet, CAT_EMOJI, HELP_TEXT

TEST_CHAT_ID = 9999999  # fake chat ID for local testing

TEST_MESSAGES = [
    "rm25 lunch mcdonalds",
    "grab rm12.50 to klcc",
    "rm8 nasi lemak mamak",
    "rm129 shoes parkson",
    "netflix rm17",
    "summary today",
    "summary this week",
    "how much did i spend this month",
    "help",
    "what is the weather",
]

async def simulate(sheet, text: str):
    print(f"\n{'─'*50}")
    print(f"YOU: {text}")

    parsed = await parse_message(text)
    intent = parsed.get("intent", "unknown")

    if parsed.get("is_spending") and intent == "log":
        insert_spending(
            sheet,
            chat_id=TEST_CHAT_ID,
            amount=parsed["amount"],
            category=parsed["category"],
            place=parsed.get("place") or "Unknown",
            note=parsed.get("note") or "",
        )
        emoji = CAT_EMOJI.get(parsed["category"], "📦")
        reply = (
            f"✅ Logged!\n"
            f"{emoji} {parsed['category']} — RM {parsed['amount']:.2f}\n"
            f"📍 {parsed.get('place') or 'Unknown'}\n"
            f"📝 {parsed.get('note') or '-'}"
        )

    elif intent == "summary_today":
        reply = format_summary(query_summary(sheet, TEST_CHAT_ID, "today"))

    elif intent == "summary_week":
        reply = format_summary(query_summary(sheet, TEST_CHAT_ID, "week"))

    elif intent == "summary_month":
        reply = format_summary(query_summary(sheet, TEST_CHAT_ID, "month"))

    elif intent == "help":
        reply = HELP_TEXT

    else:
        reply = "🤔 I didn't catch that."

    print(f"BOT: {reply}")

async def main():
    print("🔧 Connecting to Google Sheets...")
    sheet = init_sheet()
    print("✅ Sheet connected\n")
    print("Running test messages...\n")

    for msg in TEST_MESSAGES:
        try:
            await simulate(sheet, msg)
        except Exception as e:
            print(f"BOT: ⚠️ Error — {e}")

    print(f"\n{'─'*50}")
    print("✅ Done. Check your Google Sheet for new rows.")

if __name__ == "__main__":
    asyncio.run(main())