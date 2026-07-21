"""リサーチャー 久遠汐里: カテゴリ別RSS巡回と候補収集(標準ライブラリのみ)"""
import json
import re
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
POSTED_FILE = DATA_DIR / "posted_urls.json"

# カテゴリ定義(key → 表示名)。追加はここと SOURCES / PICKS_PER_CATEGORY へ
CATEGORIES = {
    "ai": "AI",
    "influencer": "インフルエンサー",
    "world": "時事・世界",
}

SOURCES = {
    "ai": [
        ("ITmedia AI+", "https://rss.itmedia.co.jp/rss/2.0/aiplus.xml"),
        ("Publickey", "https://www.publickey1.jp/atom.xml"),
        ("Gigazine", "https://gigazine.net/news/rss_2.0/"),
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("VentureBeat AI", "https://venturebeat.com/category/ai/feed/"),
        ("MIT Tech Review AI", "https://www.technologyreview.com/topic/artificial-intelligence/feed"),
        ("Hugging Face Blog", "https://huggingface.co/blog/feed.xml"),
        ("HN: AI/LLM", "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT+OR+Claude+OR+Gemini&points=80"),
    ],
    "influencer": [
        ("Googleニュース: インフルエンサー",
         "https://news.google.com/rss/search?q=%E3%82%A4%E3%83%B3%E3%83%95%E3%83%AB%E3%82%A8%E3%83%B3%E3%82%B5%E3%83%BC%20OR%20YouTuber%20OR%20TikToker%20OR%20VTuber&hl=ja&gl=JP&ceid=JP:ja"),    ],
    "world": [
        ("NHK 主要ニュース", "https://www.nhk.or.jp/rss/news/cat0.xml"),
        ("NHK 国際", "https://www.nhk.or.jp/rss/news/cat6.xml"),
        ("BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ],
}

# AIカテゴリだけはフィード内に雑多な記事が混ざるためキーワードで絞る
AI_KEYWORDS = [
    "AI", "人工知能", "生成AI", "LLM", "GPT", "Claude", "Gemini", "Llama",
    "OpenAI", "Anthropic", "DeepMind", "Mistral", "xAI", "Grok",
    "machine learning", "deep learning", "neural", "transformer",
    "diffusion", "agent", "エージェント", "RAG", "fine-tun",
    "マルチモーダル", "multimodal", "推論モデル", "reasoning", "半導体", "GPU",
]

MAX_AGE_HOURS = 36
UA = "Mozilla/5.0 (compatible; AITechTimesBot/1.0; +https://banksy-s2.github.io/ai-tech-times/)"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _text(elem) -> str:
    return re.sub(r"<[^>]+>", " ", "".join(elem.itertext())).strip() if elem is not None else ""


def _parse_date(s: str):
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        pass
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
        return r.read()


def _parse_feed(source: str, raw: bytes) -> list[dict]:
    root = ET.fromstring(raw)
    items = []
    for elem in root.iter():
        if _local(elem.tag) not in ("item", "entry"):
            continue
        title = link = summary = date_s = ""
        for child in elem:
            name = _local(child.tag)
            if name == "title":
                title = _text(child)
            elif name == "link":
                link = child.get("href") or _text(child)
            elif name in ("description", "summary", "content"):
                summary = summary or _text(child)
            elif name in ("pubDate", "published", "updated", "date"):
                date_s = date_s or _text(child)
        if title and link:
            items.append({
                "source": source,
                "title": title,
                "url": link.strip(),
                "summary": summary[:500],
                "published": date_s,
            })
    return items


def collect(category: str) -> list[dict]:
    """指定カテゴリのソースを巡回し、新鮮で未報の候補を返す"""
    posted = set(json.loads(POSTED_FILE.read_text(encoding="utf-8"))) if POSTED_FILE.exists() else set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=MAX_AGE_HOURS)
    candidates, seen = [], set()
    for source, url in SOURCES[category]:
        try:
            items = _parse_feed(source, _fetch(url))
        except Exception as e:
            print(f"  [collect:{category}] {source} 取得失敗: {e}")
            continue
        fresh = 0
        for it in items:
            dt = _parse_date(it["published"])
            if dt is not None:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
            if it["url"] in posted or it["url"] in seen:
                continue
            if category == "ai":
                text = f"{it['title']} {it['summary']}"
                if not any(k.lower() in text.lower() for k in AI_KEYWORDS):
                    continue
            it["category"] = category
            seen.add(it["url"])
            candidates.append(it)
            fresh += 1
        print(f"  [collect:{category}] {source}: {fresh}件")
    return candidates


def mark_posted(urls: list[str]) -> None:
    posted = json.loads(POSTED_FILE.read_text(encoding="utf-8")) if POSTED_FILE.exists() else []
    posted = (posted + urls)[-2000:]
    POSTED_FILE.parent.mkdir(parents=True, exist_ok=True)
    POSTED_FILE.write_text(json.dumps(posted, ensure_ascii=False, indent=1), encoding="utf-8")
