import httpx
import base64
import json
import re
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, GEMINI_MODEL, TELEGRAM_API

_client = genai.Client(api_key=GEMINI_API_KEY)

_RECEIPT_PROMPT = """\
You are reading a receipt image for a Malaysian user's expense tracker.
Extract the spending details and return ONLY valid JSON, no markdown, no extra text.

JSON keys:
- amount    : float  (total amount paid in RM; look for TOTAL, JUMLAH, AMOUNT DUE)
- category  : one of [Food, Drinks, Groceries, Clothing, Transport, Entertainment, Health, Bills, Other]
- place     : string (merchant/store name from the receipt)
- note      : string (max 8 words describing what was purchased)
- items     : list of strings (top 3 line items if visible, else empty list)
- confidence: "high" | "medium" | "low" (how confident you are in the total amount)

If you cannot read the receipt or find a total, set amount to null.

Example output:
{
  "amount": 45.80,
  "category": "Food",
  "place": "McDonald's Sunway",
  "note": "fast food meal combo",
  "items": ["McValue Meal", "McFlurry", "Fries"],
  "confidence": "high"
}
"""


async def download_photo(file_id: str) -> bytes:
    """Download a Telegram photo by file_id and return raw bytes."""
    async with httpx.AsyncClient() as client:
        # Step 1: get file path
        r = await client.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id})
        file_path = r.json()["result"]["file_path"]

        # Step 2: download the actual file
        token = TELEGRAM_API.split("bot")[1]
        url   = f"https://api.telegram.org/file/bot{token}/{file_path}"
        r2    = await client.get(url)
        return r2.content


async def parse_receipt(file_id: str) -> dict:
    """Download Telegram photo and extract spending info using Gemini Vision."""
    image_bytes  = await download_photo(file_id)
    image_b64    = base64.b64encode(image_bytes).decode("utf-8")

    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            types.Part.from_text(text=_RECEIPT_PROMPT),
        ],
        config=types.GenerateContentConfig(
            max_output_tokens=256,
            temperature=0.1,
        ),
    )

    raw = re.sub(r"```json|```", "", response.text).strip()
    return json.loads(raw)