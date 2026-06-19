import json
from datetime import datetime, timedelta
from config import HISTORY_FILE

class HistoryStore:
    def __init__(self):
        self._load()

    def _load(self):
        if HISTORY_FILE.exists() and HISTORY_FILE.stat().st_size > 0:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = []

    def _save(self):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_posted(self, url):
        return any(item.get("url") == url for item in self.data)

    def is_title_posted(self, title):
        return any(item.get("title") == title for item in self.data)

    def mark_posted(self, item):
        self.data.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "source": item.get("source", ""),
            "posted_at": datetime.now().isoformat(),
        })
        self._trim(200)
        self._save()

    def _trim(self, max_items=200):
        if len(self.data) > max_items:
            self.data = self.data[-max_items:]

    def get_recent(self, days=7):
        cutoff = datetime.now() - timedelta(days=days)
        return [item for item in self.data if datetime.fromisoformat(item["posted_at"]) > cutoff]

    def count(self):
        return len(self.data)

history = HistoryStore()
