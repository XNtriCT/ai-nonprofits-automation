import time
import random
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from config import cfg
from history_store import history

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/119.0.0.0 Safari/537.36",
]

HEADERS = lambda: {
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

ALL_QUERIES = [
    "artificial intelligence",
    "AI breakthrough",
    "AI technology news",
    "machine learning",
    "AI healthcare",
    "AI climate",
    "AI education",
    "AI ethics regulation",
    "AI research",
    "AI robots",
    "AI startups",
    "deep learning",
    "generative AI",
    "AI policy government",
    "AI science discovery",
    "AI business productivity",
    "large language model",
    "AI open source",
    "AI energy sustainability",
    "AI agriculture food",
    "AI Africa",
    "AI India",
    "AI China",
    "AI Europe",
    "AI Global South",
    "AI economy jobs",
]

NONPROFIT_QUERIES = [
    "AI nonprofit social impact",
    "AI for good",
    "AI humanitarian",
    "AI developing countries",
    "AI accessibility",
]

MAX_RESULTS_PER_QUERY = 5


def _parse_rfc2822(date_str):
    """Parse RFC 2822 date string to datetime (with UTC fallback)."""
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return None


def fetch_google_news_rss(query, max_results=MAX_RESULTS_PER_QUERY):
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
    try:
        resp = requests.get(url, headers=HEADERS(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        results = []
        for item in items[:max_results]:
            title = item.title.text.strip() if item.title else ""
            link = item.link.text.strip() if item.link else ""
            raw_date = item.pubDate.text.strip() if item.pubDate else ""
            source = item.source.text.strip() if item.source else ""
            desc = item.description.text.strip() if item.description else ""
            clean_desc = re.sub(r"<[^>]+>", "", desc) if desc else ""
            if not title or not link:
                continue
            pub_dt = _parse_rfc2822(raw_date)
            results.append({
                "title": title,
                "url": link,
                "source": source or "Google News",
                "summary": clean_desc[:500],
                "published_dt": pub_dt,
                "published": pub_dt.isoformat() if pub_dt else "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        return results
    except Exception as e:
        print(f"  [rss] {query[:35]} -> {e}")
        return []


def fetch_hn_top_ai(limit=15):
    try:
        resp = requests.get(
            "https://hn.algolia.com/api/v1/search_by_date",
            params={
                "query": "AI artificial intelligence",
                "tags": "story",
                "hitsPerPage": limit * 2,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            points = hit.get("points", 0)
            created_at = hit.get("created_at", "")
            pub_dt = _parse_rfc2822(created_at) or datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else None
            results.append({
                "title": title,
                "url": url,
                "source": "Hacker News",
                "summary": f"Points: {points}" if points else "",
                "published_dt": pub_dt,
                "published": pub_dt.isoformat() if pub_dt else "",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
        return results
    except Exception as e:
        print(f"  [hn] Error: {e}")
        return []


def _title_similarity(t1, t2):
    t1 = re.sub(r'[^a-z0-9\s]', '', t1.lower()).strip()
    t2 = re.sub(r'[^a-z0-9\s]', '', t2.lower()).strip()
    words1 = set(t1.split())
    words2 = set(t2.split())
    if len(words1) < 3 or len(words2) < 3:
        return False
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) > 0.45


def deduplicate_and_filter(news_list):
    seen_urls = set()
    seen_titles = []
    filtered = []
    for item in news_list:
        url = item.get("url", "").strip().rstrip("/")
        title = item.get("title", "").strip()
        if not url or not title:
            continue
        if url in seen_urls:
            continue
        if history.is_posted(url) or history.is_title_posted(title):
            continue
        similar = any(_title_similarity(title, t) for t in seen_titles)
        if similar:
            continue
        seen_urls.add(url)
        seen_titles.append(title)
        filtered.append(item)
    return filtered


def fetch_all_news(max_per_query=MAX_RESULTS_PER_QUERY):
    num_broad = random.randint(5, 9)
    chosen = random.sample(ALL_QUERIES, min(num_broad, len(ALL_QUERIES)))
    chosen.extend(NONPROFIT_QUERIES)
    random.shuffle(chosen)

    print(f"[news] Searching {len(chosen)} topics...")

    all_news = []
    for query in chosen:
        results = fetch_google_news_rss(query, max_per_query)
        all_news.extend(results)
        time.sleep(random.uniform(0.8, 1.8))

    hn = fetch_hn_top_ai(limit=max_per_query * 3)
    all_news.extend(hn)

    unique = deduplicate_and_filter(all_news)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=7)
    filtered = []
    for n in unique:
        dt = n.get("published_dt")
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt and dt < cutoff:
            continue
        filtered.append(n)

    filtered.sort(key=lambda x: x.get("published_dt") or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return filtered


def print_news(news):
    print(f"\n{'='*60}")
    print(f"  Fresh AI News (last 7 days) — {len(news)} items")
    print(f"{'='*60}")
    for i, n in enumerate(news[:12], 1):
        pub = n.get("published", "")[:16] if n.get("published") else "recent"
        print(f"  {i}. {n['title']}")
        print(f"     {n['source']} | {pub}")
        print()


if __name__ == "__main__":
    news = fetch_all_news()
    print_news(news)
