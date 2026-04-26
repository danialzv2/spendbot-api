import os
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

load_dotenv()

# ── Credentials ───────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GSHEET_NAME    = os.environ.get("GSHEET_NAME", "SpendBot")
GSHEET_CREDS   = os.environ["GSHEET_CREDS"]

# ── Derived ───────────────────────────────────────────────────────────────────
TELEGRAM_API   = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
GEMINI_MODEL   = "gemini-2.5-flash-preview-05-20"

# ── Timezone ──────────────────────────────────────────────────────────────────
MY_TZ = ZoneInfo("Asia/Kuala_Lumpur")   # UTC+8

# ── Category emoji map ────────────────────────────────────────────────────────
CAT_EMOJI = {
    "Food":          "🍜",
    "Drinks":        "🧋",
    "Groceries":     "🛒",
    "Electronics":   "💻",
    "Clothing":      "👕",
    "Transport":     "🚗",
    "Entertainment": "🎮",
    "Health":        "💊",
    "Bills":         "📄",
    "Education":     "📚",
    "Other":         "📦",
}