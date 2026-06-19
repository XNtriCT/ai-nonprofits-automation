import os
import requests
from config import cfg


def send_photo_to_telegram(image_path, caption):
    token = cfg.TELEGRAM_BOT_TOKEN
    chat_id = cfg.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping send.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    if not os.path.exists(image_path):
        print(f"[telegram] Image not found: {image_path}")
        return False

    max_caption_len = 1024
    if len(caption) > max_caption_len:
        caption = caption[:max_caption_len - 3] + "..."

    try:
        with open(image_path, "rb") as img:
            files = {"photo": img}
            data = {
                "chat_id": chat_id,
                "caption": caption,
                "parse_mode": "HTML",
            }
            resp = requests.post(url, files=files, data=data, timeout=60)
            resp.raise_for_status()
            result = resp.json()
            if result.get("ok"):
                print("[telegram] Message sent successfully")
                return True
            else:
                print(f"[telegram] API error: {result}")
                return False
    except Exception as e:
        print(f"[telegram] Error sending message: {e}")
        return False


def send_text_to_telegram(text):
    token = cfg.TELEGRAM_BOT_TOKEN
    chat_id = cfg.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        print("[telegram] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set. Skipping send.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }, timeout=30)
        resp.raise_for_status()
        print("[telegram] Text message sent")
        return resp.json().get("ok", False)
    except Exception as e:
        print(f"[telegram] Error sending text: {e}")
        return False


if __name__ == "__main__":
    print("Telegram module loaded. Configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to send messages.")
