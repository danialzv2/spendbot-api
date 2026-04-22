# 💸 AI Spending Tracker

Log your spending in Telegram using plain language. Gemini parses it, Google Sheets stores it, Streamlit visualises it.

**Fully free — no credit card needed.**

---

## 🏗 Architecture

```
You (Telegram)
    ↓  message
Telegram Bot API
    ↓  webhook POST
FastAPI on Render (free)
    ↓  parse with
Gemini 2.5 Flash (free)
    ↓  write row to
Google Sheets (free)
    ↓  read by
Streamlit Dashboard on Streamlit Cloud (free)
```

---

## 📁 Project Structure

```
AI SPENDING TRAC.../
├── app/
│   ├── .env                  ← your local secrets (never commit)
│   ├── .env.example          ← template to copy from
│   ├── .gitignore
│   ├── main.py               ← FastAPI webhook server
│   └── requirements.txt
├── streamlit_dashboard/
│   ├── .streamlit/
│   │   └── secrets.toml.example
│   ├── .env.example
│   ├── app.py                ← Streamlit dashboard
│   └── requirements.txt
├── .gitignore
├── README.md
├── render.yaml               ← Render deployment config
├── register_webhook.py       ← run once to connect Telegram
└── test_local.py             ← local testing without Telegram
```

> **Two GitHub repos recommended:**
> - `spendbot-api` → contains `app/` + `render.yaml` + `register_webhook.py`
> - `spendbot-dashboard` → contains `streamlit_dashboard/`

---

## 🚀 Setup Guide

### STEP 1 — Create Telegram Bot (2 min)

1. Open Telegram → search `@BotFather`
2. Send `/newbot` → follow prompts
3. Copy the **HTTP API token** → this is your `TELEGRAM_TOKEN`
4. Find your own chat ID by messaging `@userinfobot`

---

### STEP 2 — Get Gemini API Key (2 min)

1. Go to → https://aistudio.google.com/app/apikey
2. Click **Create API Key** (free, 1500 req/day)
3. Save as `GEMINI_API_KEY`

---
9a56ef94e04e1f2265901dcb607cf3095237c574
### STEP 3 — Set Up Google Sheets (10 min)

**A. Create the sheet**
1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Rename it to: `SpendBot`
4. Leave it empty — headers are auto-created on first run

**B. Create a Google Cloud Service Account**
1. Go to https://console.cloud.google.com
2. Create or select a project
3. Enable these two APIs:
   - Google Sheets API
   - Google Drive API
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Give it any name, click through to finish
6. Click the service account → **Keys tab → Add Key → JSON**
7. Download the JSON file — keep it safe

**C. Share the sheet with the service account**
1. Open the downloaded JSON, copy the `client_email` value
2. Open your `SpendBot` Google Sheet → Share
3. Paste the email → set role to **Editor** → Send

**D. Prepare the JSON for your .env**

Open the JSON file, copy the entire contents, then minify it to a single line (use https://jsonformatter.org/json-minify). This single-line string is your `GSHEET_CREDS` value.

---

### STEP 4 — Local Testing (before deploying)

```bash
# 1. Copy and fill in your secrets
cp app/.env.example app/.env
# Edit app/.env with your real TELEGRAM_TOKEN, GEMINI_API_KEY, GSHEET_CREDS

# 2. Install dependencies
pip install -r app/requirements.txt

# 3. Run the test script (no Telegram or webhook needed)
python test_local.py
# ✅ Should show "Logged!" for spending messages and summaries

# 4. Run the FastAPI server locally
cd app
uvicorn main:app --reload --port 8000
# Visit http://localhost:8000 → should return {"status": "SpendBot is running 🚀"}

# 5. Test the dashboard locally
cp streamlit_dashboard/.env.example streamlit_dashboard/.env
# Edit streamlit_dashboard/.env with your GSHEET_CREDS and GSHEET_NAME
cd streamlit_dashboard
streamlit run app.py
```

---

### STEP 5 — Deploy FastAPI to Render (5 min)

1. Push your repo to GitHub (make sure `.env` is gitignored ✅)
2. Go to https://render.com → **New → Web Service**
3. Connect your GitHub repo
4. Settings:
   - **Root directory:** `app`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free
5. Go to **Environment** tab → add these variables:
   | Key | Value |
   |-----|-------|
   | `TELEGRAM_TOKEN` | your bot token |
   | `GEMINI_API_KEY` | your Gemini key |
   | `GSHEET_NAME` | `SpendBot` |
   | `GSHEET_CREDS` | your minified JSON string |
6. Click **Deploy** → wait ~2 min
7. Verify at `https://your-app.onrender.com` → should show `{"status": "SpendBot is running 🚀"}`

> ⚠️ **Render free tier sleeps after 15 min of inactivity.** First message after sleep takes ~30s.
> Fix: set up a free ping at https://uptimerobot.com → monitor your `/` endpoint every 10 min.

---

### STEP 6 — Register Telegram Webhook (1 min)

```bash
python register_webhook.py \
  --token YOUR_TELEGRAM_TOKEN \
  --url https://your-app.onrender.com/webhook
```

Verify it worked:
```
https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo
```
The `url` field must show: `https://your-app.onrender.com/webhook`

✅ Send `rm25 lunch mcdonalds` to your bot — it should reply instantly!

---

### STEP 7 — Deploy Streamlit Dashboard (5 min)

1. Push `streamlit_dashboard/` to GitHub (separate repo recommended)
2. Go to https://share.streamlit.io → **New app**
3. Select repo, branch `main`, file `app.py`
4. **Advanced → Secrets**, paste:
```toml
GSHEET_NAME = "SpendBot"
GSHEET_CREDS = '{"type":"service_account",...}'
```
5. Click **Deploy** 🚀

---

## 💬 Bot Commands

| Message | Result |
|---------|--------|
| `rm25 lunch mcdonalds` | Logs RM25 · Food · McDonald's |
| `grab rm12.50 to klcc` | Logs RM12.50 · Transport · Grab |
| `rm8 nasi lemak` | Logs RM8 · Food |
| `rm129 shoes parkson` | Logs RM129 · Shopping · Parkson |
| `netflix rm17` | Logs RM17 · Bills · Netflix |
| `summary today` | Today's total by category |
| `summary this week` | Last 7 days breakdown |
| `summary this month` | Last 30 days breakdown |
| `help` | Show all commands |

---

## 🗄 Google Sheet Schema

Headers are auto-created on first run:

| timestamp | chat_id | amount | category | place | note |
|-----------|---------|--------|----------|-------|------|
| 2025-04-22 12:30:00 | 123456789 | 25.0 | Food | McDonald's | lunch at McDonald's |

---

## 🚨 Anomaly Detection

The dashboard uses z-score per category. Any transaction more than 2 standard deviations above the mean for its category is flagged with a 🚨 banner. Requires at least 3 transactions per category to activate.

---

## 💰 Cost Breakdown

| Service | Cost |
|---------|------|
| Telegram Bot API | Free |
| Gemini 2.5 Flash | Free (1500 req/day) |
| Google Sheets | Free |
| Render Web Service | Free |
| Streamlit Cloud | Free |
| **Total** | **RM 0 / month** |