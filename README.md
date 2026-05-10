# 💸 SpendBot — AI Spending Tracker

> Log spending in Telegram with plain language. Gemini parses it. Google Sheets stores it. Streamlit visualises it.

**100% free. No credit card. No infrastructure to manage.**

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)
![Google Cloud Run](https://img.shields.io/badge/Cloud_Run-Deployed-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini_3.1_Flash_Lite-AI-8E75B2?style=flat-square&logo=google&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ What It Does

Send a casual message to your Telegram bot — SpendBot understands it, logs it to Google Sheets, and keeps your dashboard updated in real time.

```
You:      rm25 lunch mcdonalds
SpendBot: ✅ Logged! 2025-05-09 13:22:00
          🍜 Food — RM 25.00
          📍 McDonald's
          📝 lunch at McDonald's
```

```
You:      my salary is rm4000, am i overspending?
SpendBot: 🤔 Analysing your spending data...
          Based on your RM 847 spend this month across 23 transactions,
          your daily average is RM 38.50 — that's 46% of a healthy
          daily budget on RM 4000/month. Food (42%) and Transport (28%)
          are your top two categories...
```

📸 **Receipt scanning** — just send a photo, SpendBot reads the total automatically.

---

## 🏗️ Architecture

```
You (Telegram)
      │
      ▼  plain language message / receipt photo
Telegram Bot API
      │
      ▼  webhook POST
FastAPI  ──────────────────────────────────────────  Google Cloud Run
      │                                              (auto-deploys from GitHub)
      ▼  parse intent + extract amount/category
Gemini 3.1 Flash Lite Preview (free, 500 req/day)
      │
      ▼  append row
Google Sheets (SpendBot spreadsheet)
      │
      ▼  read + visualise
Streamlit Dashboard  ──────────────────────────────  Streamlit Cloud (free)
```

---

## 📁 Project Structure

```
spendbot/
├── app/                        # FastAPI backend → deployed to Cloud Run
│   ├── main.py                 # webhook server & request routing
│   ├── gemini.py               # Gemini intent parsing with fallback models
│   ├── advisor.py              # AI financial advisor
│   ├── receipt.py              # receipt image parser (Gemini Vision)
│   ├── sheets.py               # Google Sheets read/write + analytics
│   ├── telegram.py             # message formatting & send helpers
│   ├── config.py               # env vars, constants, category emoji map
│   ├── requirements.txt
│   └── .env.example
├── streamlit_dashboard/        # Streamlit frontend → deployed to Streamlit Cloud
│   ├── app.py                  # dashboard UI
│   ├── requirements.txt
│   └── .streamlit/
│       └── secrets.toml.example
├── register_webhook.py         # run once after deploy to connect Telegram
├── .gitignore
└── README.md
```

---

## 🤖 Bot Commands

| Message | What Happens |
|---------|-------------|
| `rm25 lunch mcdonalds` | Logs RM25 · Food · McDonald's |
| `grab rm12.50 to klcc` | Logs RM12.50 · Transport · Grab |
| `rm8 nasi lemak` | Logs RM8 · Food |
| `netflix rm17` | Logs RM17 · Bills · Netflix |
| `rm129 shoes parkson` | Logs RM129 · Shopping · Parkson |
| `summary today` | Today's total by category |
| `summary this week` | Last 7 days breakdown |
| `summary this month` | Last 30 days breakdown |
| `how much should i save daily?` | AI financial advice |
| `my salary is rm4000, am i overspending?` | Contextual AI advice |
| `can i afford rm800 rent?` | Personalised projection |
| `help` | Show all commands |
| 📸 *(send a receipt photo)* | Auto-reads and logs the total |

---

## 🚀 Setup Guide

### Prerequisites

- A Google account
- A Telegram account
- A GitHub account
- Python 3.11+ (for local testing only)

---

### STEP 1 — Create Your Telegram Bot `(2 min)`

1. Open Telegram → search **`@BotFather`**
2. Send `/newbot` → follow the prompts
3. Copy the **HTTP API token** — this is your `TELEGRAM_TOKEN`
4. Find your chat ID by messaging **`@userinfobot`**

---

### STEP 2 — Get a Gemini API Key `(2 min)`

1. Go to → https://aistudio.google.com/app/apikey
2. Click **Create API Key**
3. Save it as `GEMINI_API_KEY`

> Free tier: 500 requests/day — more than enough for personal use.

---

### STEP 3 — Set Up Google Sheets `(10 min)`

**A. Create the spreadsheet**

1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Rename it to `SpendBot`
4. Leave it empty — headers are auto-created on first run

**B. Create a Service Account**

1. Go to https://console.cloud.google.com
2. Create or select a project
3. Enable these APIs under **APIs & Services → Enable APIs**:
   - Google Sheets API
   - Google Drive API
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Give it any name → click through to finish
6. Click the service account → **Keys tab → Add Key → JSON**
7. Download the JSON file — keep it safe

**C. Share the sheet with the service account**

1. Open the downloaded JSON → copy the `client_email` value
2. Open your `SpendBot` Google Sheet → click **Share**
3. Paste the `client_email` → set role to **Editor** → Send

**D. Minify the credentials JSON**

1. Open the JSON file → copy the entire contents
2. Paste into → https://jsonformatter.org/json-minify
3. Copy the output — this single-line string is your `GSHEET_CREDS`

> ⚠️ Never commit the JSON file or `.env` to GitHub. Both are in `.gitignore` already.

---

### STEP 4 — Local Testing `(optional but recommended)`

```bash
# Clone the repo
git clone https://github.com/yourusername/spendbot.git
cd spendbot

# Set up secrets
cp app/.env.example app/.env
# Edit app/.env — fill in TELEGRAM_TOKEN, GEMINI_API_KEY, GSHEET_CREDS, GSHEET_NAME

# Install and run the API
pip install -r app/requirements.txt
cd app
uvicorn main:app --reload --port 8000
# → Visit http://localhost:8000
# → Should return {"status": "SpendBot is running 🚀"}

# Run the dashboard (separate terminal)
pip install -r streamlit_dashboard/requirements.txt
cd streamlit_dashboard
streamlit run app.py
```

---

### STEP 5 — Deploy API to Google Cloud Run `(10 min)`

> No Dockerfile needed — Cloud Run auto-detects Python via Google Buildpacks.

**A. Open Cloud Run**

1. Go to https://console.cloud.google.com
2. Search **"Cloud Run"** in the top bar → click it
3. Click **"Create Service"**

**B. Connect to GitHub**

1. Select **"Continuously deploy from a repository"**
2. Click **"Set up with Cloud Build"**
3. Repository Provider → select `GitHub`
4. Click **"Authenticate"** → log into GitHub when prompted
5. Select your SpendBot repo → click **"Next"**

**C. Configure the Build**

| Field | Value |
|-------|-------|
| Branch | `^main$` |
| Build Type | `Python via Google Cloud Buildpacks` |
| Build context directory | `/app` |

Click **"Save"**

**D. Configure the Service**

| Field | Value |
|-------|-------|
| Service name | `spendbot-api` |
| Region | `asia-southeast1` *(Singapore — closest to Malaysia)* |
| Authentication | ✅ `Allow unauthenticated invocations` |

**E. Container Settings**

Click **"Container, Networking, Security"** to expand:

| Field | Value |
|-------|-------|
| Container port | `8080` |
| Memory | `512 MiB` |
| CPU | `1` |
| Startup CPU boost | ✅ **On** *(reduces cold start time, free)* |

**F. Add Environment Variables**

Click **"Variables & Secrets"** tab → **"Add Variable"** for each:

| Name | Value |
|------|-------|
| `TELEGRAM_TOKEN` | your bot token |
| `GEMINI_API_KEY` | your Gemini key |
| `GSHEET_NAME` | `SpendBot` |
| `GSHEET_CREDS` | your minified single-line JSON string |

**G. Configure Autoscaling**

Click **"Autoscaling"** tab:

| Field | Value |
|-------|-------|
| Minimum instances | `0` *(scales to zero when idle — stays free)* |
| Maximum instances | `3` |

**H. Deploy**

Click **"Create"** — first build takes ~3-5 minutes.

When done, you get a URL like:
```
https://spendbot-api-xxxxxxxx-as.a.run.app
```

Verify it's live:
```
https://spendbot-api-xxxxxxxx-as.a.run.app
→ {"status": "SpendBot is running 🚀"}
```

---

### STEP 6 — Keep It Warm with UptimeRobot `(2 min)`

Cloud Run scales to zero when idle, causing a cold start delay on the first request after inactivity. UptimeRobot pings your API every 5 minutes to keep the container warm — for free.

1. Sign up at https://uptimerobot.com (free)
2. Click **"Add New Monitor"**

| Field | Value |
|-------|-------|
| Monitor Type | `HTTP(s)` |
| Friendly Name | `SpendBot API` |
| URL | `https://your-app.a.run.app/` |
| Monitoring Interval | `5 minutes` |

3. Click **"Create Monitor"** ✅

> **Bonus:** UptimeRobot emails you if your bot ever goes down.

---

### STEP 7 — Register Telegram Webhook `(1 min)`

```bash
python register_webhook.py \
  --token YOUR_TELEGRAM_TOKEN \
  --url https://spendbot-api-xxxxxxxx-as.a.run.app/webhook
```

Verify it worked:

```
https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo
```

The `url` field must show your Cloud Run URL ending in `/webhook`.

✅ Send `rm25 lunch mcdonalds` to your bot — it should reply instantly!

---

### STEP 8 — Deploy Streamlit Dashboard `(5 min)`

1. Push `streamlit_dashboard/` to GitHub *(separate repo recommended)*
2. Go to https://share.streamlit.io → **New app**
3. Select your repo → branch `main` → file `app.py`
4. Go to **Advanced settings → Secrets** and paste:

```toml
GSHEET_NAME = "SpendBot"
GSHEET_CREDS = '{"type":"service_account",...your minified JSON...}'
```

5. Click **Deploy** 🚀

---

## 🔄 Continuous Deployment

After initial setup, every push to `main` auto-deploys with zero downtime:

```
git add .
git commit -m "feat: your change"
git push origin main

        ↓  Cloud Build triggers automatically (~2-3 min)

New revision built → deployed → traffic shifts once healthy
```

Monitor deployments:
- **Cloud Run** → your service → **Revisions tab**
- **Cloud Build** → **History tab**

---

## 🗄️ Google Sheet Schema

Headers are auto-created on first transaction:

| timestamp | chat_id | amount | category | place | note |
|-----------|---------|--------|----------|-------|------|
| 2025-05-09 13:22:00 | 123456789 | 25.0 | Food | McDonald's | lunch at McDonald's |

---

## 🚨 Anomaly Detection

The dashboard flags unusual transactions using **z-score per category**. Any transaction more than 2 standard deviations above your category mean is highlighted with a 🚨 banner.

> Requires at least 3 transactions per category to activate.

---

## 🔧 Troubleshooting

**Cloud Build fails on first deploy**
- Check: Cloud Run → your service → **Logs tab**
- Most common cause: `GSHEET_CREDS` contains line breaks — must be a single line
- Re-minify at https://jsonformatter.org/json-minify → update the env var in Cloud Run console

**Bot doesn't reply to messages**
- Confirm webhook: `https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo`
- Ensure Authentication is set to **"Allow unauthenticated invocations"**
- Check Cloud Run logs for errors

**Dashboard shows no data**
- Confirm the service account `client_email` has **Editor** access to your sheet
- Check `GSHEET_NAME` matches your sheet name exactly (case-sensitive)

**Updating env vars without redeploying**

Via console: Cloud Run → your service → **Edit & Deploy New Revision → Variables & Secrets**

Via CLI:
```bash
gcloud run services update spendbot-api \
  --region=asia-southeast1 \
  --update-env-vars KEY=VALUE
```

---

## 💰 Cost Breakdown

| Service | Free Tier | Our Usage |
|---------|-----------|-----------|
| Telegram Bot API | Unlimited | ✅ Free |
| Gemini 2.5 Flash | 1,500 req/day | ✅ Free |
| Google Sheets API | Unlimited reads/writes | ✅ Free |
| Google Cloud Run | 2M req/month + 180K vCPU-sec | ✅ Free |
| Streamlit Cloud | Unlimited public apps | ✅ Free |
| UptimeRobot | 50 monitors, 5 min interval | ✅ Free |
| **Total** | | **RM 0 / month** |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Bot interface | Telegram Bot API |
| Backend | FastAPI + Python 3.11 |
| AI parsing | Google Gemini 3.1 Flash Lite (`google-genai`) |
| Receipt scanning | Gemini Vision (multimodal) |
| Storage | Google Sheets (`gspread`) |
| Hosting | Google Cloud Run (serverless) |
| CI/CD | GitHub → Cloud Build (auto-deploy) |
| Dashboard | Streamlit |
| Keep-alive | UptimeRobot |

---

## 📄 License

MIT — free to use, modify, and distribute.

---

> Built to stop wondering where the money went. 💸