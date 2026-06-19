"""Run this script to verify the setup works."""

import os
import sys
import json

print("=" * 50)
print("AI for Nonprofits — Setup Verification")
print("=" * 50)

# 1. Check config
print("\n[1] Checking configuration...")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import cfg
print(f"  FreeLLMAPI: {cfg.FREELLMAPI_BASE}")
print(f"  Model: {cfg.FREELLMAPI_MODEL}")
print(f"  Brave: {os.path.exists(cfg.BRAVE_PATH)}")
print(f"  Brave User Data: {os.path.exists(cfg.BRAVE_USER_DATA)}")
tg_ok = bool(cfg.TELEGRAM_BOT_TOKEN and cfg.TELEGRAM_CHAT_ID)
print(f"  Telegram configured: {tg_ok}")

# 2. Test FreeLLMAPI
print("\n[2] Testing FreeLLMAPI connection...")
import requests
try:
    r = requests.post(f"{cfg.FREELLMAPI_BASE}/chat/completions",
        json={
            "model": cfg.FREELLMAPI_MODEL,
            "messages": [{"role": "user", "content": "Say hello in one word"}],
            "max_tokens": 20,
        }, timeout=15)
    if r.status_code == 200:
        reply = r.json()["choices"][0]["message"]["content"]
        print(f"  OK — Response: {reply}")
    else:
        print(f"  ERROR — Status {r.status_code}: {r.text[:200]}")
except Exception as e:
    print(f"  ERROR — {e}")

# 3. Test news fetching
print("\n[3] Testing news fetcher...")
from news_fetcher import fetch_all_news
try:
    news = fetch_all_news(max_per_query=2)
    print(f"  Found {len(news)} new items")
    for n in news[:3]:
        print(f"    • {n['title'][:80]}...")
except Exception as e:
    print(f"  ERROR — {e}")

# 4. Test caption generation (dry run)
print("\n[4] Testing caption generator (1 call)...")
from caption_generator import generate_caption
try:
    test_news = {
        "title": "India launches AI-powered telemedicine network for rural villages",
        "url": "https://example.com",
        "summary": "India has launched a nationwide AI-powered telemedicine network connecting rural villages to specialist doctors using machine learning diagnostics.",
    }
    caption = generate_caption(test_news)
    if caption:
        print(f"  OK — Caption ({len(caption)} chars)")
        print(f"  Preview: {caption[:100]}...")
    else:
        print("  FAILED — No caption returned")
except Exception as e:
    print(f"  ERROR — {e}")

# 5. Test image prompt generation (dry run)
print("\n[5] Testing image prompt generator (1 call)...")
from image_prompt_gen import generate_image_prompt
try:
    prompt = generate_image_prompt(test_news, caption or "Test caption")
    if prompt:
        print(f"  OK — Prompt ({len(prompt)} chars)")
        print(f"  Preview: {prompt[:100]}...")
    else:
        print("  FAILED — No prompt returned")
except Exception as e:
    print(f"  ERROR — {e}")

print("\n" + "=" * 50)
print("Setup verification complete!")
print("=" * 50)
