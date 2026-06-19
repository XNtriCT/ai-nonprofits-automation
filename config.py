import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DOWNLOADS_DIR = BASE_DIR / "downloads"
HISTORY_FILE = DATA_DIR / "history.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]")

class Config:
    FREELLMAPI_BASE = os.getenv("FREELLMAPI_BASE", "http://172.24.197.38:3001/v1")
    FREELLMAPI_KEY = os.getenv("FREELLMAPI_KEY", "freellmapi-c8622568e26da22a29187a370a863297a231ce423929b7ad")
    FREELLMAPI_MODEL = os.getenv("FREELLMAPI_MODEL", "gpt-4o")

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    BRAVE_PATH = os.getenv("BRAVE_PATH", r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")

    MAX_POSTS_PER_RUN = int(os.getenv("MAX_POSTS_PER_RUN", "1"))

cfg = Config()
