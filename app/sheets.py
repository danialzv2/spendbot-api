import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from config import GSHEET_CREDS, GSHEET_NAME, MY_TZ

_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

def init_sheet():
    """Authenticate and return the first sheet, creating headers if needed."""
    import re as _re
    creds_raw = GSHEET_CREDS

    # Normalize the private key — replace any actual newlines inside the key
    # with literal \n so json.loads can parse it cleanly
    def fix_private_key(s: str) -> str:
        match = _re.search(r'"private_key"\s*:\s*"(.*?)"(?=\s*,)', s, _re.DOTALL)
        if match:
            key_val = match.group(1)
            key_fixed = key_val.replace('\n', '\\n').replace('\r', '')
            s = s[:match.start(1)] + key_fixed + s[match.end(1):]
        return s

    creds_raw = fix_private_key(creds_raw)
    creds_dict = json.loads(creds_raw)
    creds  = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    client = gspread.authorize(creds)
    sheet  = client.open(GSHEET_NAME).sheet1

    if not sheet.row_values(1):
        sheet.append_row(
            ["timestamp", "chat_id", "amount", "category", "place", "note"],
            value_input_option="USER_ENTERED"
        )
    return sheet


def insert_spending(
    sheet,
    chat_id:  int,
    amount:   float,
    category: str,
    place:    str,
    note:     str,
) -> str:
    """Append a spending row using Malaysia time. Returns the timestamp string."""
    now_my = datetime.now(MY_TZ).strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row(
        [now_my, str(chat_id), amount, category, place, note],
        value_input_option="USER_ENTERED"
    )
    return now_my


def query_summary(sheet, chat_id: int, period: str = "month") -> dict:
    """Return spending breakdown for today / week / month in Malaysia time."""
    records = sheet.get_all_records()
    now_my  = datetime.now(MY_TZ)

    if period == "today":
        cutoff = now_my.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        cutoff = now_my - timedelta(days=7)
    else:
        cutoff = now_my - timedelta(days=30)

    breakdown: dict[str, float] = {}
    total = 0.0

    for row in records:
        if str(row.get("chat_id")) != str(chat_id):
            continue
        try:
            # Timestamps stored as MYT — parse as naive then treat as MYT
            ts_naive = datetime.strptime(str(row["timestamp"]), "%Y-%m-%d %H:%M:%S")
            ts_my    = ts_naive.replace(tzinfo=MY_TZ)
        except Exception:
            continue
        if ts_my < cutoff:
            continue

        cat = row.get("category", "Other")
        amt = float(row.get("amount", 0))
        breakdown[cat] = breakdown.get(cat, 0.0) + amt
        total += amt

    breakdown = dict(sorted(breakdown.items(), key=lambda x: x[1], reverse=True))
    return {"total": total, "breakdown": breakdown, "period": period}