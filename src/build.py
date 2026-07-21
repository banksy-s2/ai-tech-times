"""開発部長 八重樫慧: data/articles.json から静的サイトをdocs/に全再生成"""
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "articles.json"
DOCS = ROOT / "docs"

SITE_NAME = "AI TECH TIMES"
BASE_URL = "https://banksy-s2.github.io/ai-tech-times"
TAGLINE = "AIが編集するAI・テックニュース。毎朝7時更新。"
JST = timezone(timedelta(hours=9))

CSS = """
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;--accent2:#f78166}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:"Hiragino Sans","Yu Gothic UI","Noto Sans JP",sans-serif;line-height:1.8}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--border);padding:28px 0;margin-bottom:32px}
.logo{font-size:1.7rem;font-weight:800;letter-spacing:.05em;color:var(--text)}
.logo span{color:var(--accent2)}
.tagline{color:var(--muted);font-size:.85rem;margin-top:4px}
.date-head{font-size:.9rem;color:var(--muted);margin:24px 0 12px;border-left:3px solid var(--accent2);padding-left:10px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px 24px;margin-bottom:16px;transition:border-color .2s}
.card:hover{border-color:var(--accent)}
.card h2{font-size:1.15rem;margin-bottom:8px}
.card h2 a{color:var(--text)}
.card .lead{color:var(--muted);font-size:.92rem}
.meta{font-size:.78rem;color:var(--muted);margin-top:10px}
.tag{display:inline-block;background:#1f2937;border-radius:20px;padding:1px 10px;margin-right:6px;font-size:.75rem;color:var(--accent)}
article h1{font-size:1.6rem;line-height:1.5;margin-bottom:12px}
article .lead{color:var(--muted);font-size:1rem;border-left:3px solid var(--accent2);padding-left:12px;margin:16px 0}
article p{margin:16px 0}
.source{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-size:.85rem;margin-top:28px}
footer{border-top:1px solid var(--border);margin-top:48px;padding:24px 0;color:var(--muted);font-size:.8rem;text-align:center}
.back{display:inline-block;margin:20px 0;font-size:.9rem}
"""


def _load() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return []


def _page(title: str, desc: str, path: str, body: str, jsonld: str = "") -> str:
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE_URL}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{BASE_URL}{path}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="article">
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE_URL}/feed.xml">
<link rel="stylesheet" href="{BASE_URL}/style.css">
{jsonld}
</head>
<body>
<header><div class="wrap">
<a href="{BASE_URL}/" class="logo">AI TECH <span>TIMES</span></a>
<div class="tagline">{TAGLINE}</div>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">© 2026 {SITE_NAME} — AI編集部が自動収集・執筆しています。事実確認は出典元をご参照ください。<br>
<a href="{BASE_URL}/about.html">このサイトについて</a> / <a href="{BASE_URL}/feed.xml">RSS</a></div></footer>
</body>
</html>"""


def _article_html(a: dict) -> str:
    e = html.escape
    paragraphs = "\n".join(f"<p>{e(p)}</p>" for p in a["body"])
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"], "description": a["lead"],
        "datePublished": a["date"], "inLanguage": "ja",
        "author": {"@type": "Organization", "name": f"{SITE_NAME} 編集部"},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": f"{BASE_URL}{a['path']}",
        "isBasedOn": a["source_url"],
    }, ensure_ascii=False)
    body = f"""<a class="back" href="{BASE_URL}/">← トップに戻る</a>
<article>
<h1>{e(a['title'])}</h1>
<div class="meta">{a['date']} / {tags}</div>
<div class="lead">{e(a['lead'])}</div>
{paragraphs}
<div class="source">出典: <a href="{e(a['source_url'])}" rel="noopener" target="_blank">{e(a['source'])} — 元記事を読む</a></div>
</article>"""
    return _page(f"{a['title']} | {SITE_NAME}", a["lead"], a["path"], body,
                 f'<script type="application/ld+json">{jsonld}</script>')


def _index_html(arts: list[dict]) -> str:
    e = html.escape
    cards, last_date = [], None
    for a in arts[:60]:
        if a["date"] != last_date:
            cards.append(f'<div class="date-head">{a["date"]}</div>')
            last_date = a["date"]
        tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
        cards.append(f"""<div class="card">
<h2><a href="{BASE_URL}{a['path']}">{e(a['title'])}</a></h2>
<div class="lead">{e(a['lead'])}</div>
<div class="meta">{tags} 出典: {e(a['source'])}</div>
</div>""")
    return _page(f"{SITE_NAME} — {TAGLINE}", TAGLINE, "/", "\n".join(cards))


def _about_html() -> str:
    body = f"""<article>
<h1>このサイトについて</h1>
<p>{SITE_NAME}は、AI編集部(生成AI)が国内外のテックメディアのRSSを毎朝巡回し、その日のAI・テック関連の重要ニュースを選定・執筆している自動運営ニュースサイトです。</p>
<p>記事は元記事の要約に基づいて生成されており、各記事の末尾に必ず出典リンクを明記しています。正確な情報は出典元をご確認ください。</p>
<p>更新: 毎朝7時(JST) / 運営: AI TECH TIMES 編集部</p>
</article>"""
    return _page(f"このサイトについて | {SITE_NAME}", "AI TECH TIMESの運営方針", "/about.html", body)


def _feed_xml(arts: list[dict]) -> str:
    e = html.escape
    items = "\n".join(f"""<item>
<title>{e(a['title'])}</title>
<link>{BASE_URL}{a['path']}</link>
<guid>{BASE_URL}{a['path']}</guid>
<pubDate>{datetime.strptime(a['date'], '%Y-%m-%d').replace(tzinfo=JST).strftime('%a, %d %b %Y 07:00:00 +0900')}</pubDate>
<description>{e(a['lead'])}</description>
</item>""" for a in arts[:20])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{SITE_NAME}</title>
<link>{BASE_URL}/</link>
<description>{TAGLINE}</description>
<language>ja</language>
{items}
</channel></rss>"""


def _sitemap(arts: list[dict]) -> str:
    urls = [f"{BASE_URL}/", f"{BASE_URL}/about.html"] + [f"{BASE_URL}{a['path']}" for a in arts]
    entries = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""


def _llms_txt(arts: list[dict]) -> str:
    recent = "\n".join(f"- [{a['title']}]({BASE_URL}{a['path']}): {a['lead']}" for a in arts[:15])
    return f"""# {SITE_NAME}

> {TAGLINE} 生成AIが国内外テックメディアのRSSから毎朝ニュースを選定・執筆する自動運営サイト。全記事に出典リンクあり。

## 最新記事
{recent}

## その他
- [このサイトについて]({BASE_URL}/about.html)
- [RSSフィード]({BASE_URL}/feed.xml)
"""


def build() -> None:
    arts = sorted(_load(), key=lambda a: a["date"], reverse=True)
    DOCS.mkdir(exist_ok=True)
    (DOCS / "articles").mkdir(exist_ok=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    (DOCS / "index.html").write_text(_index_html(arts), encoding="utf-8")
    (DOCS / "about.html").write_text(_about_html(), encoding="utf-8")
    (DOCS / "feed.xml").write_text(_feed_xml(arts), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(_sitemap(arts), encoding="utf-8")
    (DOCS / "llms.txt").write_text(_llms_txt(arts), encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    for a in arts:
        out = DOCS / a["path"].lstrip("/")
        out.write_text(_article_html(a), encoding="utf-8")
    print(f"  [build] {len(arts)}記事でサイト再生成完了")


def save_articles(new_arts: list[dict]) -> None:
    arts = _load()
    known = {a["path"] for a in arts}
    today = datetime.now(JST).strftime("%Y-%m-%d")
    for a in new_arts:
        a["date"] = today
        a["path"] = f"/articles/{today.replace('-', '')}-{a['slug']}.html"
        if a["path"] not in known:
            arts.append(a)
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(arts, ensure_ascii=False, indent=1), encoding="utf-8")
