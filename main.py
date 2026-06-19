#!/usr/bin/env python3
"""
AI for Nonprofits — Full Automation Pipeline

Flow:
  1. Fetch latest AI news from web
  2. Deduplicate against history
  3. Generate caption via LLM
  4. Generate image prompt via LLM
  5. Generate image via ChatGPT (Playwright + Brave)
  6. Send to Telegram
  7. Record in history
"""

import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path

from config import cfg, DOWNLOADS_DIR
from news_fetcher import fetch_all_news
from caption_generator import generate_caption
from image_prompt_gen import generate_image_prompt
from image_generator import generate_image
from telegram_sender import send_photo_to_telegram, send_text_to_telegram
from history_store import history


def run_pipeline(dry_run=False, custom_topic=None, logo_path=None, logo_corner="br"):
    print("=" * 60)
    print(f"  AI for Nonprofits — Pipeline Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if custom_topic:
        print(f"\n[1/5] Custom topic: {custom_topic}")
        news_items = [{"title": custom_topic, "source": "custom", "url": "", "published": datetime.now().isoformat()}]
    else:
        print("\n[1/5] Fetching latest AI news...")
        news_items = fetch_all_news(max_per_query=5)
        print(f"  Found {len(news_items)} new, unposted news items")

    if not news_items:
        print("  No new news to process.")
        if custom_topic:
            print("  Nothing to process.")
        else:
            send_text_to_telegram("🤖 AI for Nonprofits: No new news found today. Check back tomorrow!")
        return

    for idx in range(min(len(news_items), cfg.MAX_POSTS_PER_RUN)):
        news = news_items[idx]
        print(f"\n--- Post {idx + 1}/{cfg.MAX_POSTS_PER_RUN} ---")
        print(f"  Title: {news['title']}")
        print(f"  Source: {news['source']}")

        print("\n[2/5] Generating caption...")
        caption = generate_caption(news)
        if not caption:
            print("  Failed to generate caption, skipping...")
            continue
        print(f"  Caption:\n{caption}\n")

        print("[3/5] Generating image prompt...")
        image_prompt = generate_image_prompt(news, caption)
        if not image_prompt:
            print("  Failed to generate image prompt, skipping...")
            continue
        print(f"  Image prompt:\n{image_prompt[:200]}...\n")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in news["title"][:40] if c.isalnum() or c in " _-").strip()
        output_path = os.path.join(DOWNLOADS_DIR, f"post_{timestamp}_{safe_title}.png")

        print("[4/5] Generating image via ChatGPT (Brave browser)...")
        if dry_run:
            print("  [DRY RUN] Skipping actual image generation")
            image_path = None
        else:
            start = time.time()
            image_path = generate_image(image_prompt, output_path, logo_path, logo_corner)
            elapsed = time.time() - start
            print(f"  Image generated in {elapsed:.1f}s: {image_path}")

        if image_path and os.path.exists(image_path):
            print("\n[5/5] Image ready:")
            print(f"  File: {image_path}")
            print(f"  Caption:\n{caption}\n")
            full_caption = f"{caption}\n\nvia AI for Nonprofits"
            success = send_photo_to_telegram(image_path, full_caption)
            if success:
                history.mark_posted(news)
                print("  Posted to Telegram!")
            else:
                history.mark_posted(news)
                print("  Image saved locally (Telegram not configured or failed). Marked as posted.")
        else:
            print("\n[5/5] No image generated. News NOT marked as posted — will retry next run.")

        print("\n" + "=" * 60)

    print(f"\nPipeline complete. Total posted today: {cfg.MAX_POSTS_PER_RUN}")
    print(f"Total history size: {history.count()} items")


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    custom_topic = None
    for i, a in enumerate(sys.argv):
        if a == "--topic" and i + 1 < len(sys.argv):
            custom_topic = sys.argv[i + 1]
    run_pipeline(dry_run=dry_run, custom_topic=custom_topic)
