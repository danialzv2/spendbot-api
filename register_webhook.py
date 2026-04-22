#!/usr/bin/env python3
"""
register_webhook.py
Run this ONCE after deploying to Azure App Service to connect your bot.

Usage:
    python register_webhook.py \
        --token YOUR_TELEGRAM_TOKEN \
        --url https://your-app.azurewebsites.net/webhook
"""
import argparse
import httpx

def register(token: str, webhook_url: str):
    api = f"https://api.telegram.org/bot{token}"

    # Set webhook
    r = httpx.post(f"{api}/setWebhook", json={"url": webhook_url})
    print("setWebhook:", r.json())

    # Confirm
    r2 = httpx.get(f"{api}/getWebhookInfo")
    print("getWebhookInfo:", r2.json())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    parser.add_argument("--url",   required=True)
    args = parser.parse_args()
    register(args.token, args.url)