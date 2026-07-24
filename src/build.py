"""開発部長 八重樫慧: data/ から静的サイトをdocs/に全再生成"""
import hashlib
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import buzz, ogp, storage, terms as terms_mod
from .collect import CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "articles.json"
DOCS = ROOT / "docs"

SITE_NAME = "AI TECH TIMES"
BASE_URL = "https://ai-tech-times.web.app"
TAGLINE = "眠らない編集部が、世界を一時間ごとに読み解く。"
JST = timezone(timedelta(hours=9))

FIREBASE_CONFIG = '{"apiKey":"AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s","authDomain":"ai-tech-times.firebaseapp.com","projectId":"ai-tech-times"}'
FIREBASE_SDK = """<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js"></script>"""

NAV = [("/", "トップ"), ("/popular.html", "人気"), ("/ai.html", "海外AI"), ("/ai_jp.html", "日本のAI"),
       ("/silicon.html", "シリコンバレー"), ("/voices.html", "海外AIの声"),
       ("/influencer.html", "インフルエンサー"), ("/world.html", "時事・世界"),
       ("/stock.html", "株式投資"), ("/jp_corp.html", "日本企業"),
       ("/buzz.html", "バズ動画TOP10"), ("/term/", "AI用語事典"), ("/office.html", "編集部ライブ")]

# 検索(SEO)用のページタイトルと説明文。ブランド名は後ろ、検索されるキーワードを先頭に
INDEX_TITLE = f"AIニュース速報・生成AIの最新情報まとめ | {SITE_NAME}"
INDEX_DESC = "生成AI・ChatGPT・Claude・シリコンバレーの最新ニュースを毎時更新。海外AI識者の発信やバズ動画ランキングも日本語でまとめてお届け。"
CATEGORY_SEO = {
    "ai": (f"海外AIニュース速報(日本語訳) | {SITE_NAME}",
           "OpenAI、Anthropic、Google、NVIDIAなど海外AI業界の最新動向を日本語で毎日速報。海外一次ソースから翻訳してお届け。"),
    "ai_jp": (f"日本のAIニュース・国内企業のAI活用最前線 | {SITE_NAME}",
              "日本企業のAI活用、国産AIモデル、国内のAI規制・政策の最新ニュースを毎日更新。"),
    "silicon": (f"シリコンバレー最新ニュース速報(日本語訳) | {SITE_NAME}",
                "TechmemeやTechCrunchなど米テック速報を日本語で毎日翻訳。買収・資金調達・新製品などシリコンバレーの今がわかる。"),
    "voices": (f"海外AI研究者・識者の最新発信まとめ | {SITE_NAME}",
               "Simon Willison、Andrej Karpathyら海外AI識者の一次発信を日本語で紹介。日本ではまだ知られていない視点を毎日お届け。"),
    "influencer": (f"インフルエンサー・YouTuber・VTuberの最新ニュース | {SITE_NAME}",
                   "国内外のインフルエンサー、YouTuber、TikToker、VTuberの話題を毎日更新。"),
    "world": (f"今日の重要ニュース・世界情勢まとめ | {SITE_NAME}",
              "NHK・BBCから今日知っておくべき時事・国際ニュースを厳選して毎日お届け。"),
    "stock": (f"日本株・株式投資の最新ニュース(日経平均・東証) | {SITE_NAME}",
              "日経平均・東証・日本株の最新動向、日銀・金利・為替・決算・NISAなど投資家が知っておきたい国内ニュースを毎日更新。"),
    "jp_corp": (f"日本の上場企業の最新ニュース(決算・提携・買収) | {SITE_NAME}",
                "トヨタ・ソニーなど日本の上場企業の決算、業務提携、買収、新事業、不祥事まで、企業の動きを毎日更新。"),
}
BUZZ_TITLE = f"世界でバズってるYouTube動画ランキングTOP10(毎日更新) | {SITE_NAME}"

CSS = """
:root{
 --bg:#0A0E1A;--card:#141A2B;--card2:#1B2236;--border:#242C42;
 --text:#ECE8DF;--muted:#8E94AC;--dim:#5D6480;
 --accent:#F6B23C;--accent2:#FF4635;--gold:#E9B44C;--signal:#FF4635;--amber:#F6B23C;
 --mono:ui-monospace,"SFMono-Regular","Cascadia Mono","Consolas","Courier New",monospace;
 --sans:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic UI","Noto Sans JP",sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--text);font-family:var(--sans);line-height:1.8;background-image:radial-gradient(1200px 400px at 50% -120px,rgba(246,178,60,.06),transparent 70%)}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:880px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--border);padding:22px 0 0;position:relative}
header::before{content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--signal),var(--amber) 60%,transparent)}
.mast{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.logo{font-size:1.85rem;font-weight:900;letter-spacing:-.01em;color:var(--text)}
.logo span{color:var(--amber)}
.mast-tag{font-family:var(--mono);font-size:.62rem;letter-spacing:.22em;color:var(--amber);border:1px solid var(--border);border-radius:4px;padding:3px 8px;text-transform:uppercase;white-space:nowrap}
.tagline{color:var(--muted);font-size:.86rem;margin-top:6px;letter-spacing:.01em}
nav{display:flex;gap:2px;margin-top:14px;overflow-x:auto;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav a{font-family:var(--mono);color:var(--muted);font-size:.8rem;letter-spacing:.04em;padding:9px 13px;border-bottom:2px solid transparent;white-space:nowrap;transition:color .15s}
nav a:hover{color:var(--text)}
nav a.on{color:var(--text);border-bottom-color:var(--amber)}
main{margin-top:24px}
.livewire{background:linear-gradient(180deg,var(--card2),var(--card));border:1px solid var(--border);border-left:3px solid var(--signal);border-radius:12px;padding:14px 18px;margin-bottom:22px;box-shadow:0 10px 30px -18px rgba(255,70,53,.5)}
.lw-status{display:flex;align-items:center;gap:10px;font-family:var(--mono);font-size:.74rem;letter-spacing:.06em;color:var(--muted);margin-bottom:10px;flex-wrap:wrap}
.lw-dot{width:9px;height:9px;border-radius:50%;background:var(--signal);animation:lwpulse 1.8s infinite}
@keyframes lwpulse{0%{box-shadow:0 0 0 0 rgba(255,70,53,.55)}70%{box-shadow:0 0 0 8px rgba(255,70,53,0)}100%{box-shadow:0 0 0 0 rgba(255,70,53,0)}}
.lw-live{color:var(--signal);font-weight:700}
.lw-status b{color:var(--amber);font-weight:600}
.lw-head a{display:block;color:var(--text);padding:5px 0;font-size:.98rem;line-height:1.6;border-top:1px dashed var(--border)}
.lw-head a:first-child{border-top:none}
.lw-head a:hover{color:var(--amber)}
.lw-head .arw{color:var(--signal);font-family:var(--mono);margin-right:8px}
.date-head{font-family:var(--mono);font-size:.82rem;color:var(--amber);letter-spacing:.06em;margin:28px 0 14px;display:flex;align-items:center;gap:10px}
.date-head::before{content:"";width:6px;height:6px;background:var(--signal);border-radius:50%;flex:none}
.date-head a{color:inherit}
.date-head a:last-child{color:var(--dim)}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:22px 24px;margin-bottom:14px;transition:border-color .2s,transform .2s,background .2s}
.card:hover{border-color:var(--amber);background:var(--card2);transform:translateY(-2px)}
.card h2{font-size:1.22rem;font-weight:800;line-height:1.5;margin-bottom:8px;letter-spacing:-.005em}
.card h2 a{color:var(--text)}
.card:hover h2 a{color:#fff}
.card .lead{color:var(--muted);font-size:.92rem;line-height:1.7}
.meta{font-family:var(--mono);font-size:.72rem;color:var(--dim);margin-top:12px;letter-spacing:.03em}
.ctime{color:var(--amber);font-weight:700;margin-right:8px}
.tag{display:inline-block;color:var(--muted);margin-right:8px;font-size:.74rem}
.tag::before{content:"#";color:var(--dim)}
.cat{display:inline-block;font-family:var(--mono);color:var(--amber);border:1px solid rgba(246,178,60,.35);border-radius:4px;padding:1px 8px;margin-right:8px;font-size:.68rem;letter-spacing:.08em;font-weight:600;vertical-align:middle}
.newb{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);color:var(--signal);font-size:.68rem;font-weight:700;letter-spacing:.12em;margin-right:9px;vertical-align:middle}
.newb::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--signal);animation:lwpulse 1.6s infinite}
article h1{font-size:1.85rem;font-weight:900;line-height:1.45;margin-bottom:14px;letter-spacing:-.01em}
article .lead{color:var(--muted);font-size:1.02rem;border-left:3px solid var(--amber);padding-left:14px;margin:18px 0}
article p{margin:16px 0;font-size:1.02rem}
.source{background:var(--card);border:1px solid var(--border);border-left:3px solid var(--dim);border-radius:8px;padding:12px 16px;font-size:.85rem;margin-top:30px}
.sum3{background:var(--card2);border:1px solid var(--border);border-left:3px solid var(--amber);border-radius:10px;padding:14px 18px;margin:18px 0}
.sum3 .s3h{font-family:var(--mono);color:var(--amber);font-size:.72rem;letter-spacing:.1em;font-weight:700;margin-bottom:8px}
.sum3 ul{list-style:none}
.sum3 li{font-size:.94rem;padding:3px 0}
.sum3 li::before{content:"\2014  ";color:var(--amber)}
.likebar{margin:18px 0 4px}
.likebtn{background:transparent;border:1.5px solid var(--signal);color:var(--signal);border-radius:24px;padding:8px 22px;font-size:.92rem;font-weight:700;cursor:pointer;transition:all .15s;font-family:var(--sans)}
.likebtn:hover{transform:scale(1.04)}
.likebtn.liked{background:var(--signal);color:#fff}
.rankp{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:12px;transition:border-color .2s}
.rankp:hover{border-color:var(--amber)}
.rankp .no{font-family:var(--mono);font-size:1.4rem;font-weight:800;color:var(--gold);min-width:2rem;text-align:center}
.rankp .lk{color:var(--signal);font-weight:700;white-space:nowrap;font-family:var(--mono)}
.rank-card{display:flex;gap:16px;background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:14px;align-items:center;transition:border-color .2s,transform .2s}
.rank-card:hover{border-color:var(--amber);transform:translateY(-2px)}
.rank-no{font-family:var(--mono);font-size:1.7rem;font-weight:800;color:var(--gold);min-width:2.2rem;text-align:center}
.rank-thumb{width:160px;min-width:160px;border-radius:8px;display:block}
.rank-body h2{font-size:1rem;line-height:1.5;margin-bottom:4px}
.rank-body h2 a{color:var(--text)}
.rank-meta{font-family:var(--mono);font-size:.76rem;color:var(--muted)}
.rank-comment{font-size:.85rem;color:var(--amber);margin-top:4px}
.person{color:var(--accent);border-bottom:1px dashed var(--accent);cursor:pointer}
.person:hover{color:#fff;border-color:#fff}
.person[data-kind="company"]{color:#6FD3A8;border-color:#6FD3A8}
.person[data-kind="ai"]{color:var(--amber);border-color:var(--amber)}
#pkind{display:inline-block;font-family:var(--mono);background:var(--card2);border-radius:4px;padding:1px 8px;margin-right:8px;font-size:.68rem;letter-spacing:.06em;color:var(--muted);vertical-align:middle}
#pbox{display:none;position:fixed;left:50%;bottom:24px;transform:translateX(-50%);width:min(92vw,480px);background:var(--card2);border:1px solid var(--amber);border-radius:14px;padding:16px 20px;z-index:99;box-shadow:0 12px 40px rgba(0,0,0,.65)}
#pbox .prow{display:flex;gap:14px;align-items:flex-start}
#pimg{display:none;width:72px;height:72px;object-fit:cover;border-radius:50%;border:2px solid var(--amber);flex-shrink:0}
#pbox b{color:var(--text);font-size:1.05rem}
#pbox p{margin:6px 0 0;font-size:.9rem;color:var(--muted)}
#plink{display:none;font-size:.78rem;margin-top:6px}
#pbox .pclose{position:absolute;top:8px;right:12px;color:var(--muted);cursor:pointer;font-size:1.1rem}
#pbox .pnote{margin-top:8px;font-size:.72rem;color:var(--dim)}
footer{border-top:1px solid var(--border);margin-top:52px;padding:26px 0;color:var(--dim);font-size:.8rem;text-align:center}
footer a{color:var(--muted)}
.back{display:inline-block;margin:20px 0;font-family:var(--mono);font-size:.82rem;color:var(--muted)}
.back:hover{color:var(--amber)}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
@media(max-width:600px){.rank-thumb{width:110px;min-width:110px}.rank-no{font-size:1.3rem;min-width:1.7rem}.logo{font-size:1.55rem}article h1{font-size:1.5rem}}
"""
CSS_VER = hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]


def _load() -> list[dict]:
    return storage.load_json(DATA_FILE, [])


def _jsonld(obj: dict) -> str:
    """script要素内に安全に埋め込めるJSON-LD(</script>分割を防ぐ)"""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def _iso(date: str, time: str = "07:00") -> str:
    """記事の日付+時刻をISO8601(JST)に。AI検索の鮮度シグナル用"""
    t = time if (time and ":" in time) else "07:00"
    return f"{date}T{t}:00+09:00"


PUBLISHER = {
    "@type": "Organization",
    "name": SITE_NAME,
    "url": f"{BASE_URL}/",
    "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/ogp/logo.png", "width": 512, "height": 512},
}


def _fmt_views(n: int) -> str:
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}億回再生"
    if n >= 10_000:
        return f"{n / 10_000:.0f}万回再生"
    return f"{n:,}回再生"


def _page(title: str, desc: str, path: str, body: str, jsonld: str = "", og_image: str = "/ogp/default.png") -> str:
    e = html.escape
    nav = "".join(
        f'<a href="{BASE_URL}{href}" class="{"on" if href == path or (href != "/" and path.startswith(href)) else ""}">{label}</a>'
        for href, label in NAV)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="google-site-verification" content="xU_1Ryr_326_pB2PYRmrYcU0-qprXI9QjAl2LgAlA5w">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{BASE_URL}{path}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{BASE_URL}{path}">
<meta property="og:site_name" content="{SITE_NAME}">
<meta property="og:type" content="article">
<meta property="og:image" content="{BASE_URL}{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{BASE_URL}{og_image}">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE_URL}/feed.xml">
<link rel="stylesheet" href="{BASE_URL}/style.css?v={CSS_VER}">
<script defer src="{BASE_URL}/views.js"></script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-V2T0G11PSH"></script>
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', 'G-V2T0G11PSH');
</script>
{jsonld}
</head>
<body>
<header><div class="wrap">
<div class="mast"><a href="{BASE_URL}/" class="logo">AI TECH <span>TIMES</span></a><span class="mast-tag">24H · AI-EDITED</span></div>
<div class="tagline">{TAGLINE}</div>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">© 2026 {SITE_NAME} — AI編集部が自動収集・執筆しています。事実確認は出典元をご参照ください。<br>
<a href="{BASE_URL}/digest/">分野別まとめ</a> / <a href="{BASE_URL}/weekly.html">週刊まとめ</a> / <a href="{BASE_URL}/term/">AI用語事典</a> / <a href="{BASE_URL}/buzz/">バズ動画殿堂</a> / <a href="{BASE_URL}/archive/">アーカイブ</a> / <a href="{BASE_URL}/about.html">このサイトについて</a> / <a href="{BASE_URL}/feed.xml">RSS</a></div></footer>
</body>
</html>"""


def _is_new(a: dict) -> bool:
    """直近3時間以内の記事にNEWバッジ(毎時再生成で自動的に付いて外れる)"""
    try:
        ts = datetime.strptime(f"{a['date']} {a.get('time', '07:00')}", "%Y-%m-%d %H:%M").replace(tzinfo=JST)
        diff = datetime.now(JST) - ts
        return timedelta(0) <= diff <= timedelta(hours=3)  # 未来日時はNEW扱いしない
    except ValueError:
        return False


def _cards(arts: list[dict], with_date_heads: bool = True) -> str:
    e = html.escape
    out, last_date = [], None
    for a in arts:
        if with_date_heads and a["date"] != last_date:
            out.append(f'<div class="date-head"><a href="{BASE_URL}/archive/{a["date"]}.html" style="color:inherit">{a["date"]}</a> <a href="{BASE_URL}/archive/{a["date"]}.html" style="font-size:.78rem">(この日の全記事)</a></div>')
            last_date = a["date"]
        tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
        cat = CATEGORIES.get(a.get("category", "ai"), "AI")
        newb = '<span class="newb">NEW</span>' if _is_new(a) else ""
        tm = a.get("time", "")
        tmark = f'<span class="ctime">{e(tm)}</span>' if tm else ""
        out.append(f"""<div class="card">
<h2>{newb}<a href="{BASE_URL}{a['path']}">{e(a['title'])}</a></h2>
<div class="lead">{e(a['lead'])}</div>
<div class="meta">{tmark}<span class="cat">{cat}</span>{tags} 出典: {e(a['source'])}</div>
</div>""")
    return "\n".join(out)


def _mark_entities(text: str, ents: list[dict]) -> str:
    """本文中の人物・企業・AI名をタップ可能なspanに(プレースホルダー方式で入れ子・属性破壊を防ぐ)"""
    e = html.escape
    marked = text
    for i, p in sorted(enumerate(ents), key=lambda x: -len(x[1]["name"])):
        if len(p["name"]) < 3:  # 「林」等の短名は無関係語(森林など)を巻き込むためリンク化しない
            continue
        marked = marked.replace(p["name"], f"\x00{i}\x01")
    out = e(marked)
    for i, p in enumerate(ents):
        span = (f'<span class="person" data-kind="{e(p["kind"])}" data-bio="{e(p["bio"])}">'
                f'{e(p["name"])}</span>')
        out = out.replace(f"\x00{i}\x01", span)
    return out


KIND_LABEL = {"person": "人物", "company": "企業", "ai": "AI"}


def _article_html(a: dict) -> str:
    e = html.escape
    ents = ([{"name": p["name"], "bio": p["bio"], "kind": "person"}
             for p in a.get("people", []) if isinstance(p, dict)]
            + [{"name": t["name"], "bio": t["desc"], "kind": t["type"]}
               for t in a.get("terms", []) if isinstance(t, dict) and t.get("type") in ("company", "ai")])
    people = ents  # 以降の存在判定に使用
    paragraphs = "\n".join(f"<p>{_mark_entities(p, ents)}</p>" for p in a["body"])
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
    cat = CATEGORIES.get(a.get("category", "ai"), "AI")
    art_id = a["path"].rsplit("/", 1)[-1].replace(".html", "")
    iso = _iso(a["date"], a.get("time", "07:00"))
    og_img = ogp.generate(a) or "/ogp/default.png"  # 生成失敗時は実在するデフォルトへ
    news_ld = {
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"], "description": a["lead"],
        "image": [f"{BASE_URL}{og_img}"],
        "datePublished": iso, "dateModified": iso, "inLanguage": "ja",
        "articleSection": cat, "keywords": ", ".join(a.get("tags", [])),
        "author": {"@type": "Organization", "name": f"{SITE_NAME} 編集部", "url": f"{BASE_URL}/about.html"},
        "publisher": PUBLISHER,
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{BASE_URL}{a['path']}"},
        "isBasedOn": a["source_url"],
    }
    if a.get("summary3"):
        news_ld["abstract"] = " ".join(a["summary3"])
    breadcrumb = {
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": f"{BASE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": cat, "item": f"{BASE_URL}/{a.get('category', 'ai')}.html"},
            {"@type": "ListItem", "position": 3, "name": a["title"]},
        ],
    }
    jsonld = _jsonld(news_ld) + '</script>\n<script type="application/ld+json">' + _jsonld(breadcrumb)
    src_url = a["source_url"]
    if src_url.startswith(("http://", "https://")):  # javascript:等の不正スキームはリンク化しない
        source = f'<a href="{e(src_url)}" rel="noopener" target="_blank">{e(a["source"])} — 元記事を読む</a>'
    else:
        source = e(a["source"])
    body = f"""<a class="back" href="{BASE_URL}/">← トップに戻る</a>
<article>
<h1>{e(a['title'])}</h1>
<div class="meta"><span class="cat">{cat}</span><time datetime="{iso}">{a['date']} {a.get('time', '')} 更新</time> / {tags}</div>
<div class="likebar"><button class="likebtn" id="likebtn" onclick="doLike()">♥ いいね <span id="likecount"></span></button></div>
{('<div class="sum3"><div class="s3h">⚡ 3行まとめ</div><ul>' + ''.join(f'<li>{e(s)}</li>' for s in a.get('summary3', [])) + '</ul></div>') if a.get('summary3') else ''}
<div class="lead">{e(a['lead'])}</div>
{paragraphs}
<div class="source">出典: {source}</div>
</article>
{FIREBASE_SDK}
<script>window.__ART = {json.dumps({"id": art_id, "title": a["title"], "path": a["path"], "cat": cat}, ensure_ascii=False).replace("</", "<\\/")};</script>
<script src="{BASE_URL}/likes.js"></script>"""
    if people:
        body += """
<div id="pbox"><span class="pclose" onclick="this.parentNode.style.display='none'">✕</span>
<div class="prow"><img id="pimg" alt=""><div><span id="pkind"></span><b id="pname"></b><p id="pbio"></p>
<a id="plink" target="_blank" rel="noopener">Wikipediaで見る →</a>
<div id="prel" style="margin-top:8px;font-size:.82rem"></div></div></div>
<div class="pnote">※AI編集部によるメモです。画像はWikipediaより。正確な情報はご自身でもご確認ください。</div></div>
<script>
var pcache = {}, pcur = "", pidx = null;
function prelated(name){
  var box = document.getElementById("prel");
  box.textContent = "";
  function show(idx){
    var here = location.pathname.split("/").pop().replace(".html", "");
    var base = name.replace(/(氏|さん|様|社)$/, "");  // 表記ゆれ(氏・社付き)でも一致させる
    var hits = Object.keys(idx).filter(function(k){
      return k !== here && idx[k].title.indexOf(base) >= 0;
    }).slice(0, 3);
    if (!hits.length) return;
    var h = document.createElement("div");
    h.textContent = "この話題の記事:";
    h.style.color = "var(--muted)";
    box.appendChild(h);
    hits.forEach(function(k){
      var a = document.createElement("a");
      a.href = "__BASE__" + idx[k].path;
      a.textContent = "・" + idx[k].title;
      a.style.display = "block";
      box.appendChild(a);
    });
  }
  if (pidx) { show(pidx); return; }
  fetch("__BASE__/articles_index.json").then(function(r){ return r.json(); })
    .then(function(idx){ pidx = idx; show(idx); }).catch(function(){});
}
function papply(name, info){
  if (name !== pcur) return;
  var img = document.getElementById("pimg"), lnk = document.getElementById("plink");
  if (info.img) { img.src = info.img; img.style.display = "block"; } else { img.style.display = "none"; }
  if (info.url) { lnk.href = info.url; lnk.style.display = "inline-block"; } else { lnk.style.display = "none"; }
}
function ngr(s){var t=(s||"").replace(/[\\s、。・]/g,"");var o={};for(var i=0;i<t.length-1;i++)o[t.substr(i,2)]=1;return o;}
function novl(a,b){var A=ngr(a),B=ngr(b),n=0;for(var k in A)if(B[k])n++;return n;}
function pwiki(name, bio){
  var key = name.replace(/(氏|さん|様|CEO|会長|社長|大統領|首相|大臣|監督|選手|議員)$/, "");
  if (pcache[key]) { papply(name, pcache[key]); return; }
  // 候補5件のWikipedia説明文とAI紹介文を突き合わせ、内容が一致する項目だけ採用(同名別物対策)
  fetch("https://ja.wikipedia.org/w/api.php?action=query&list=search&format=json&origin=*&srlimit=5&srsearch=" + encodeURIComponent(key))
    .then(function(r){ return r.json(); })
    .then(function(d){
      var hits = (d.query && d.query.search) || [];
      if (!hits.length) { pcache[key] = {}; papply(name, {}); return; }
      return Promise.all(hits.slice(0, 4).map(function(h){
        return fetch("https://ja.wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(h.title))
          .then(function(r){ return r.json(); }).catch(function(){ return null; });
      })).then(function(sums){
        var best = null, bestScore = 2;  // 最低3点未満は不採用=写真なし
        sums.forEach(function(s){
          if (!s) return;
          var desc = (s.description || "") + " " + (s.extract || "").slice(0, 200) + " " + s.title;
          var score = novl(bio + " " + key, desc);
          if (score > bestScore) { bestScore = score; best = s; }
        });
        var info = best ? {img: best.thumbnail && best.thumbnail.source,
                           url: best.content_urls && best.content_urls.desktop && best.content_urls.desktop.page} : {};
        pcache[key] = info; papply(name, info);
      });
    }).catch(function(){});
}
document.addEventListener("click", function(ev){
  var t = ev.target;
  var box = document.getElementById("pbox");
  if (t.classList && t.classList.contains("person")) {
    pcur = t.textContent;
    var kinds = {person: "人物", company: "企業", ai: "AI"};
    document.getElementById("pkind").textContent = kinds[t.getAttribute("data-kind")] || "";
    document.getElementById("pname").textContent = t.textContent;
    document.getElementById("pbio").textContent = t.getAttribute("data-bio");
    document.getElementById("pimg").style.display = "none";
    document.getElementById("plink").style.display = "none";
    box.style.display = "block";
    pwiki(t.textContent, t.getAttribute("data-bio"));
    prelated(t.textContent);
  } else if (!t.closest("#pbox")) {
    box.style.display = "none";
  }
});
</script>""".replace("__BASE__", BASE_URL)
    og = og_img  # 上で生成済み(二重生成しない)
    return _page(f"{a['title']} | {SITE_NAME}", a["lead"], a["path"], body,
                 f'<script type="application/ld+json">{jsonld}</script>', og_image=og)


def _buzz_html(data: dict) -> str:
    e = html.escape
    rows = []
    for v in data.get("videos", []):
        regions = "・".join(v.get("regions", [])[:4])
        comment = f'<div class="rank-comment">{e(v["comment"])}</div>' if v.get("comment") else ""
        rows.append(f"""<div class="rank-card">
<div class="rank-no">{v['rank']}</div>
<a href="{e(v['url'])}" rel="noopener" target="_blank"><img class="rank-thumb" src="{e(v['thumb'])}" alt="{e(v['title'])}" loading="lazy"></a>
<div class="rank-body">
<h2><a href="{e(v['url'])}" rel="noopener" target="_blank">{e(v['title'])}</a></h2>
<div class="rank-meta">{e(v['channel'])} / {_fmt_views(v['views'])} / 急上昇: {regions}</div>
{comment}
</div>
</div>""")
    date = data.get("date") or "未集計"
    vids = data.get("videos", [])
    top = vids[0] if vids else None
    multi = [v for v in vids if len(v.get("regions", [])) >= 3]
    jsonld = _jsonld({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f"世界のバズ動画TOP10 ({date})",
        "description": "世界6地域のYouTube急上昇を統合した、今世界でバズっている動画のランキング。",
        "numberOfItems": len(vids),
        "itemListElement": [
            {"@type": "ListItem", "position": v["rank"], "url": v["url"], "name": v["title"]}
            for v in vids
        ],
    })
    faq = _jsonld({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "今世界で一番バズっている動画は？",
             "acceptedAnswer": {"@type": "Answer", "text":
                (f"{date}時点の1位は「{top['title']}」({top['channel']}、{_fmt_views(top['views'])})です。"
                 f"世界6地域のYouTube急上昇を統合して集計しました。" if top else "集計中です。")}},
            {"@type": "Question", "name": "このランキングはどうやって集計していますか？",
             "acceptedAnswer": {"@type": "Answer", "text":
                "アメリカ・イギリス・日本・韓国・ブラジル・インドの6地域のYouTube急上昇を毎時取得し、"
                "複数地域でランクインしている動画を優先しつつ再生回数順に統合しています。"}},
        ],
    })
    summary = ""
    if top:
        multi_txt = (f"うち{len(multi)}本は3地域以上で同時に急上昇しており、国境を越えて広がっています。" if multi else "")
        summary = f'''<div class="sum3"><div class="s3h">⚡ {date}のまとめ</div><p style="margin:6px 0 0">
今世界で最もバズっている動画は「{e(top['title'])}」({e(top['channel'])}／{_fmt_views(top['views'])})です。{multi_txt}
このランキングは米・英・日・韓・伯・印の6地域のYouTube急上昇を毎時集計して統合したものです。</p></div>'''
    body = f"""<article>
<h1>世界のバズ動画TOP10</h1>
<div class="meta">{date} 集計 / 毎時更新 / <a href="{BASE_URL}/buzz/">過去のランキング・殿堂入りを見る</a></div>
{summary}
</article>
{''.join(rows) if rows else '<p>本日の集計はまだありません。</p>'}
<p style="margin-top:24px"><a href="{BASE_URL}/buzz/">→ 日別アーカイブと殿堂入りランキング</a></p>"""
    return _page(BUZZ_TITLE,
                 f"今世界でバズっている動画TOP10({date}時点の1位は「{top['title'][:24]}」)。米・英・日・韓・伯・印6地域のYouTube急上昇を毎時集計。" if top
                 else "世界6地域のYouTube急上昇を毎時集計したバズ動画ランキング。",
                 "/buzz.html", body,
                 f'<script type="application/ld+json">{jsonld}</script>\n<script type="application/ld+json">{faq}</script>')


def _buzz_archive_html(hist: dict, hof: list[dict]) -> str:
    """バズ動画の日別アーカイブ+殿堂入り。独自データを検索資産に変える"""
    e = html.escape
    hof_rows = []
    for i, v in enumerate(hof, 1):
        span = f"{v['first']}〜{v['last']}" if v["first"] != v["last"] else v["first"]
        hof_rows.append(f"""<div class="rank-card">
<div class="rank-no">{i}</div>
<a href="{e(v['url'])}" rel="noopener" target="_blank"><img class="rank-thumb" src="{e(v['thumb'])}" alt="{e(v['title'])}" loading="lazy"></a>
<div class="rank-body">
<h2><a href="{e(v['url'])}" rel="noopener" target="_blank">{e(v['title'])}</a></h2>
<div class="rank-meta">{e(v['channel'])} / TOP10入り{v['days']}日 / 最高{v['best']}位 / {_fmt_views(v['views'])}</div>
<div class="rank-comment">{span}</div>
</div>
</div>""")
    day_rows = []
    for day in sorted(hist, reverse=True)[:60]:
        rows = sorted(hist[day], key=lambda r: r["rank"])
        top3 = "／".join(e(r["title"][:26]) for r in rows[:3])
        day_rows.append(f'<div class="card"><h2>{day}のTOP10</h2><div class="lead">1位〜3位: {top3}</div>'
                        f'<div class="meta">{len(rows)}本を記録</div></div>')
    body = f"""<a class="back" href="{BASE_URL}/buzz.html">← 今日のランキングへ</a>
<article>
<h1>バズ動画の殿堂入り・日別アーカイブ</h1>
<div class="meta">{len(hist)}日分の記録 / 米・英・日・韓・伯・印の6地域を毎時集計</div>
<div class="sum3"><div class="s3h">⚡ 殿堂入りとは</div><p style="margin:6px 0 0">
世界6地域のYouTube急上昇TOP10に、何日間ランクインし続けたかで並べたランキングです。
一瞬の瞬間風速ではなく「長く世界で愛された動画」がわかります。</p></div>
</article>
<h2 style="margin:28px 0 14px;font-size:1.1rem">殿堂入り(TOP10入り日数順)</h2>
{''.join(hof_rows) if hof_rows else '<p>集計中です。</p>'}
<h2 style="margin:32px 0 14px;font-size:1.1rem">日別の記録</h2>
{''.join(day_rows) if day_rows else '<p>まだ記録がありません。</p>'}"""
    return _page(f"バズ動画の殿堂入り・過去ランキング一覧 | {SITE_NAME}",
                 "世界6地域のYouTube急上昇TOP10に長くランクインし続けた動画の殿堂入りランキングと、日別のバズ動画アーカイブ。",
                 "/buzz/index.html", body)


VIEWS_JS = """(function(){
 try{
  var id = location.pathname.replace(/[^a-zA-Z0-9\\-_.]/g, "_").replace(/^_+|_+$/g, "") || "home";
  // JST日付: UTCに9時間を足してISO文字列のUTC日付部を読む(閲覧者のタイムゾーンに依存しない)
  var d = new Date(Date.now() + 9*3600*1000).toISOString().slice(0,10).replace(/-/g, "");
  var k = "v:" + d + ":" + id;
  if (sessionStorage.getItem(k)) return;  // 同一セッション内の再読込は数えない
  sessionStorage.setItem(k, "1");
  var doc = "projects/ai-tech-times/databases/(default)/documents/views/" + d;
  fetch("https://firestore.googleapis.com/v1/projects/ai-tech-times/databases/(default)/documents:commit?key=__KEY__", {
    method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({writes: [{transform: {document: doc, fieldTransforms: [
      {fieldPath: "total", increment: {integerValue: "1"}},
      {fieldPath: "pages.`" + id + "`", increment: {integerValue: "1"}}
    ]}}]})
  }).catch(function(){});
 }catch(e){}
})();"""

LIKES_JS = """(function(){
 if (!window.firebase || !window.__ART) return;
 firebase.initializeApp(__FBCONF__);
 var db = firebase.firestore();
 var A = window.__ART, ref = db.collection("likes").doc(A.id);
 var btn = document.getElementById("likebtn"), cnt = document.getElementById("likecount");
 ref.get().then(function(d){ cnt.textContent = d.exists ? (d.data().count || 0) : 0; }).catch(function(){});
 if (localStorage.getItem("liked:" + A.id)) btn.classList.add("liked");
 window.doLike = function(){
   if (localStorage.getItem("liked:" + A.id)) return;
   btn.classList.add("liked");
   cnt.textContent = (parseInt(cnt.textContent || "0", 10) + 1);
   ref.set({count: firebase.firestore.FieldValue.increment(1), title: A.title, path: A.path, cat: A.cat}, {merge: true})
     .then(function(){ localStorage.setItem("liked:" + A.id, "1"); })
     .catch(function(){  // 失敗時は表示を戻して再試行可能にする
       btn.classList.remove("liked");
       cnt.textContent = Math.max(0, parseInt(cnt.textContent || "1", 10) - 1);
     });
 };
})();"""


def _popular_html() -> str:
    # XSS/改ざん対策: Firestoreの値は「記事ID」と「count」しか信用しない。
    # 表示するタイトル・カテゴリ・リンクはサイト側の信頼できる台帳(articles_index.json)から引く
    body = f"""<article>
<h1>人気の記事</h1>
<div class="meta">読者の「いいね」が多い順(リアルタイム集計)</div>
</article>
<div id="plist" style="margin-top:16px;color:var(--muted)">読み込み中…</div>
{FIREBASE_SDK}
<script>
firebase.initializeApp({FIREBASE_CONFIG});
Promise.all([
  fetch("{BASE_URL}/articles_index.json").then(function(r){{ return r.json(); }}),
  firebase.firestore().collection("likes").orderBy("count", "desc").limit(40).get()
]).then(function(res){{
  var index = res[0], out = [], i = 1;
  res[1].forEach(function(d){{
    if (i > 20) return;
    var meta = index[d.id];          // 台帳にないIDは表示しない(偽データ排除)
    if (!meta) return;
    var count = d.data().count;
    if (typeof count !== "number" || count < 1) return;
    var el = document.createElement("div"); el.className = "rankp";
    var no = document.createElement("div"); no.className = "no"; no.textContent = i++;
    var mid = document.createElement("div"); mid.style.flex = "1";
    var a = document.createElement("a"); a.href = "{BASE_URL}" + meta.path; a.textContent = meta.title;
    var tg = document.createElement("span"); tg.className = "tag"; tg.textContent = meta.cat;
    mid.appendChild(a); mid.appendChild(document.createTextNode(" ")); mid.appendChild(tg);
    var lk = document.createElement("div"); lk.className = "lk"; lk.textContent = "♥ " + count;
    el.appendChild(no); el.appendChild(mid); el.appendChild(lk); out.push(el);
  }});
  var box = document.getElementById("plist");
  box.textContent = "";
  if (out.length) {{ out.forEach(function(el){{ box.appendChild(el); }}); }}
  else {{ box.textContent = "まだ「いいね」された記事がありません。気に入った記事の♥を押してみてください。"; }}
}}).catch(function(){{ document.getElementById("plist").textContent = "読み込みに失敗しました"; }});
</script>"""
    return _page(f"人気の記事ランキング | {SITE_NAME}", "読者のいいねが多い人気ニュースランキング", "/popular.html", body)


def _archive_day_html(date: str, day_arts: list[dict]) -> str:
    y, m, d = date.split("-")
    title = f"{y}年{int(m)}月{int(d)}日のニュース一覧({len(day_arts)}本) | {SITE_NAME}"
    body = f"""<article>
<h1>{y}年{int(m)}月{int(d)}日のニュース</h1>
<div class="meta">この日に掲載した全{len(day_arts)}本 / <a href="{BASE_URL}/archive/">アーカイブ一覧へ</a></div>
</article>
{_cards(sorted(day_arts, key=lambda a: a.get("time", ""), reverse=True), with_date_heads=False)}"""
    return _page(title, f"{y}年{int(m)}月{int(d)}日にAI TECH TIMESが掲載したニュース{len(day_arts)}本の一覧。",
                 f"/archive/{date}.html", body)


def _archive_index_html(by_date: dict) -> str:
    months: dict = {}
    for date in sorted(by_date, reverse=True):
        months.setdefault(date[:7], []).append(date)
    sections = []
    for month, dates in months.items():
        y, m = month.split("-")
        days = "".join(
            f'<a href="{BASE_URL}/archive/{d}.html" class="tag" style="margin:3px;font-size:.85rem">{int(d[8:10])}日({len(by_date[d])}本)</a>'
            for d in dates)
        sections.append(f'<div class="card"><h2>{y}年{int(m)}月</h2><div style="margin-top:8px">{days}</div></div>')
    body = f"""<article>
<h1>ニュースアーカイブ</h1>
<div class="meta">日付ごとの全記事一覧。毎時の自動更新で増えていきます</div>
</article>
<div style="margin-top:16px">{''.join(sections)}</div>"""
    return _page(f"日別ニュースアーカイブ | {SITE_NAME}", "AI TECH TIMESの過去記事を日付ごとに一覧できるアーカイブ。",
                 "/archive/index.html", body)


KIND_JA = {"company": "企業", "ai": "AI・製品", "person": "人物"}


def _term_html(t: dict) -> str:
    """用語解説ページ。「〇〇とは」への直答+当社の報道履歴"""
    e = html.escape
    name, kind = t["name"], KIND_JA.get(t["kind"], "用語")
    alias_txt = f'<div class="meta">別名・表記ゆれ: {e("、".join(t["aliases"]))}</div>' if t["aliases"] else ""
    rows = []
    for a in t["articles"][:30]:
        cat = CATEGORIES.get(a.get("category", "ai"), "AI")
        rows.append(f'''<div class="card">
<h2><a href="{BASE_URL}{a['path']}">{e(a['title'])}</a></h2>
<div class="lead">{e(a['lead'])}</div>
<div class="meta"><span class="ctime">{a['date']} {a.get('time','')}</span><span class="cat">{cat}</span></div>
</div>''')
    body = f"""<a class="back" href="{BASE_URL}/term/">← 用語事典の一覧へ</a>
<article>
<h1>{e(name)}とは</h1>
<div class="meta"><span class="cat">{kind}</span>当サイトでの言及 {t['count']}件 / 最終更新 {t['latest']}</div>
<div class="sum3"><div class="s3h">⚡ ひとことで言うと</div><p style="margin:6px 0 0">{e(t['desc'])}</p></div>
{alias_txt}
<p>{e(name)}は、AI TECH TIMESが{t['count']}本の記事で報じてきた{kind}です。以下は当サイトが実際に報道した{e(name)}関連のニュースで、新しい順に並んでいます。用語の解説はAI編集部によるもので、各記事には一次情報へのリンクを掲載しています。</p>
</article>
<h2 style="margin:28px 0 14px;font-size:1.1rem">{e(name)}に関するニュース({t['count']}件)</h2>
{''.join(rows)}"""
    ld = _jsonld({
        "@context": "https://schema.org", "@type": "DefinedTerm",
        "name": name, "description": t["desc"], "inDefinedTermSet": f"{BASE_URL}/term/",
        "url": f"{BASE_URL}{t['url']}", "alternateName": t["aliases"],
    })
    faq = _jsonld({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": f"{name}とは？",
                        "acceptedAnswer": {"@type": "Answer", "text": t["desc"]}}],
    })
    jsonld = ld + '</script>\n<script type="application/ld+json">' + faq
    return _page(f"{name}とは？意味と最新ニュース{t['count']}件 | {SITE_NAME}",
                 f"{name}とは。{t['desc']} AI TECH TIMESが報じた{name}関連ニュース{t['count']}件をまとめています。",
                 t["url"], body, f'<script type="application/ld+json">{jsonld}</script>')


def _term_index_html(tdict: dict) -> str:
    e = html.escape
    groups: dict = {}
    for t in tdict.values():
        groups.setdefault(t["kind"], []).append(t)
    sections = []
    for kind in ("ai", "company", "person"):
        items = sorted(groups.get(kind, []), key=lambda x: -x["count"])
        if not items:
            continue
        links = "".join(
            f'<a href="{BASE_URL}{t["url"]}" class="tag" style="margin:4px;font-size:.9rem">{e(t["name"])}<span style="color:var(--dim)"> {t["count"]}</span></a>'
            for t in items)
        sections.append(f'<div class="card"><h2>{KIND_JA[kind]}({len(items)})</h2><div style="margin-top:10px">{links}</div></div>')
    body = f"""<article>
<h1>AI用語事典</h1>
<div class="meta">全{len(tdict)}語 / 記事に登場したAI・企業・人物を自動で索引化</div>
<div class="sum3"><div class="s3h">⚡ この事典について</div><p style="margin:6px 0 0">AI TECH TIMESの記事に登場したAIモデル・企業・人物を、解説と報道履歴つきで引ける事典です。毎時の更新で新しい用語が自動的に追加されます。</p></div>
</article>
<div style="margin-top:16px">{''.join(sections)}</div>"""
    return _page(f"AI用語事典 — AIモデル・企業・人物を{len(tdict)}語収録 | {SITE_NAME}",
                 f"AIモデル、テック企業、キーパーソンを{len(tdict)}語収録した用語事典。各用語の解説と、AI TECH TIMESが報じた関連ニュースをまとめて読めます。",
                 "/term/index.html", body)


def _digest_html(cat: str, arts: list[dict], tdict: dict) -> str:
    """カテゴリ横断まとめ: 「この分野で今何が起きているか」を俯瞰する。
    単発ニュースでは大手に勝てなくても、207本を持つ当社なら作れる資産ページ。"""
    e = html.escape
    label = CATEGORIES.get(cat, cat)
    cat_arts = [a for a in arts if a.get("category") == cat]
    if len(cat_arts) < 5:
        return ""
    # この分野でよく登場する用語(=論点)を抽出
    from collections import Counter
    cnt: Counter = Counter()
    for a in cat_arts:
        seen = {terms_mod.canonical(t["name"])
                for t in a.get("terms", []) + a.get("people", [])
                if isinstance(t, dict) and t.get("name")}
        cnt.update(seen)  # 記事単位で数える(同一記事内の重複を水増ししない)
    keys = [(n, c) for n, c in cnt.most_common() if c >= 2 and n in tdict][:12]
    key_rows = "".join(
        f'<div class="card"><h2><a href="{BASE_URL}{tdict[n]["url"]}">{e(n)}</a> '
        f'<span class="tag">{c}件</span></h2><div class="lead">{e(tdict[n]["desc"])}</div></div>'
        for n, c in keys)
    days = sorted({a["date"] for a in cat_arts}, reverse=True)
    latest = cat_arts[0] if cat_arts else None
    recent_rows = "".join(
        f'<div class="card"><h2><a href="{BASE_URL}{a["path"]}">{e(a["title"])}</a></h2>'
        f'<div class="lead">{e(a["lead"])}</div>'
        f'<div class="meta"><span class="ctime">{a["date"]} {a.get("time","")}</span>出典: {e(a["source"])}</div></div>'
        for a in cat_arts[:20])
    kw = "、".join(n for n, _ in keys[:6])
    intro = (f"AI TECH TIMESは{label}分野で{len(cat_arts)}本の記事を配信してきました。"
             f"この分野で繰り返し登場している論点は{kw}です。" if keys else
             f"AI TECH TIMESは{label}分野で{len(cat_arts)}本の記事を配信してきました。")
    body = f"""<article>
<h1>{label}の最新動向まとめ</h1>
<div class="meta">{len(cat_arts)}本の記事から / {days[-1]}〜{days[0]} / 毎時更新</div>
<div class="sum3"><div class="s3h">⚡ この分野の現在地</div><p style="margin:6px 0 0">{e(intro)}
{('直近の動きは「' + e(latest['title']) + '」です。') if latest else ''}</p></div>
</article>
<h2 style="margin:28px 0 14px;font-size:1.1rem">この分野のキーワード</h2>
{key_rows if key_rows else '<p>集計中です。</p>'}
<h2 style="margin:32px 0 14px;font-size:1.1rem">最近の記事({min(len(cat_arts),20)}件 / 全{len(cat_arts)}件)</h2>
{recent_rows}
<p style="margin-top:20px"><a href="{BASE_URL}/{cat}.html">→ {label}の記事一覧をすべて見る</a></p>"""
    ld = _jsonld({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": f"{label}の最新動向まとめ", "description": intro,
        "inLanguage": "ja", "isPartOf": {"@id": f"{BASE_URL}/#org"},
    })
    return _page(f"{label}の最新動向まとめ — 記事{len(cat_arts)}本から見る現在地 | {SITE_NAME}",
                 f"{label}分野で今何が起きているか。AI TECH TIMESが配信した{len(cat_arts)}本の記事から、主要な論点と最新の動きをまとめています。",
                 f"/digest/{cat}.html", body, f'<script type="application/ld+json">{ld}</script>')


def _digest_index_html(arts: list[dict]) -> str:
    e = html.escape
    from collections import Counter
    cnt = Counter(a.get("category", "ai") for a in arts)
    rows = "".join(
        f'<div class="card"><h2><a href="{BASE_URL}/digest/{c}.html">{CATEGORIES[c]}の最新動向まとめ</a></h2>'
        f'<div class="meta">{cnt[c]}本の記事から</div></div>'
        for c in CATEGORIES if cnt.get(c, 0) >= 5)
    body = f"""<article>
<h1>分野別まとめ</h1>
<div class="meta">全{len(arts)}本の記事を分野ごとに俯瞰</div>
<div class="sum3"><div class="s3h">⚡ このページについて</div><p style="margin:6px 0 0">
個別のニュースではなく「その分野で今何が起きているか」を、当サイトが配信した記事の蓄積から俯瞰するページです。毎時の更新で内容が育ちます。</p></div>
</article>
<div style="margin-top:16px">{rows}</div>"""
    return _page(f"分野別まとめ — AI・株式・企業・世界の現在地 | {SITE_NAME}",
                 "AI、シリコンバレー、株式投資、日本企業など分野ごとに「今何が起きているか」を記事の蓄積から俯瞰するまとめページ。",
                 "/digest/index.html", body)


def _weekly_html() -> str:
    from . import weekly as weekly_mod
    e = html.escape
    data = weekly_mod.load()
    rows = []
    for i, it in enumerate(data.get("items", []), 1):
        comment = f'<div class="lead">{e(it["comment"])}</div>' if it.get("comment") else ""
        rows.append(f"""<div class="rankp"><div class="no">{i}</div>
<div style="flex:1"><a href="{BASE_URL}{e(it['path'])}">{e(it['title'])}</a> <span class="tag">{e(it.get('cat', ''))}</span>{comment}</div></div>""")
    period = e(data.get("range", ""))
    body = f"""<article>
<h1>週刊まとめ — 今週の重要ニュースTOP10</h1>
<div class="meta">{period or '毎週月曜の朝に自動発行'}</div>
</article>
<div style="margin-top:16px">{''.join(rows) if rows else '<p>第1号は次の月曜朝に発行されます。</p>'}</div>"""
    return _page(f"今週のAIニュースまとめTOP10 | {SITE_NAME}",
                 "今週のAI・テック重要ニュースを編集部が10本に厳選。毎週月曜更新。",
                 "/weekly.html", body)


def _about_html() -> str:
    body = f"""<article>
<h1>このサイトについて</h1>
<p>{SITE_NAME}は、AI編集部(生成AI)が国内外のメディアのRSSとYouTube急上昇を巡回し、AI・シリコンバレー・海外AI識者・インフルエンサー・時事の重要ニュースと世界のバズ動画を選定・執筆している自動運営ニュースサイトです。</p>
<p>記事は元記事の要約に基づいて生成されており、各記事の末尾に必ず出典リンクを明記しています。正確な情報は出典元をご確認ください。</p>
<p>当サイトはサービス向上のためGoogleアナリティクスによるアクセス解析を利用しています。</p>
<p>更新: 毎時(フル更新は朝7時・昼12時・夕方5時・夜9時 JST) / 運営: AI TECH TIMES 編集部(株)</p>
<h1 style="margin-top:36px">編集部メンバー</h1>
<div class="card"><h2>灰崎 律 <span class="tag">CEO</span></h2><div class="lead">経営統括。編集方針の最終決定を担う。</div></div>
<div class="card"><h2>真行寺 環 <span class="tag">編集長</span></h2><div class="lead">その日のニュース価値を見極め、全記事を選定・執筆する。</div></div>
<div class="card"><h2>久遠 汐里 <span class="tag">リサーチャー</span></h2><div class="lead">国内外20超のソースとYouTube急上昇6地域を毎便巡回する。</div></div>
<div class="card"><h2>八重樫 慧 <span class="tag">開発部長</span></h2><div class="lead">サイト生成と配信インフラ、障害対応を担当する。</div></div>
<div class="card"><h2>桐生 まひろ <span class="tag">広報</span></h2><div class="lead">Xでの告知と日報の記録を担当する。</div></div>
</article>
<article style="margin-top:36px">
<h1>よくある質問</h1>
<div class="sum3"><div class="s3h">AI TECH TIMESとは</div><p style="margin:6px 0 0">生成AIが国内外メディアのRSSとYouTube急上昇を毎時巡回し、AI・株式・企業・時事のニュースを日本語で選定・執筆する自動運営ニュースメディアです。2026年7月21日開設。全記事に出典リンクを明記しています。</p></div>
<div class="sum3"><div class="s3h">記事はどうやって作られていますか</div><p style="margin:6px 0 0">元記事の要約に含まれる事実のみを使い、生成AI(Google Gemini)が日本語記事に再構成しています。数値や固有名詞の推測での追加は禁止し、投資助言や釣り見出しは公開前の機械検査で除外しています。海外ソースは日本語に翻訳しています。</p></div>
<div class="sum3"><div class="s3h">どのくらいの頻度で更新されますか</div><p style="margin:6px 0 0">毎時0分に自動更新しています。朝7時・昼12時・夕方5時・夜9時(日本時間)はフル更新で全カテゴリ・世界のバズ動画TOP10まで更新します。</p></div>
<div class="sum3"><div class="s3h">情報は信頼できますか</div><p style="margin:6px 0 0">各記事の末尾に一次情報(元記事)へのリンクを必ず掲載しています。当サイトはAIによる自動編集であることを明示しており、正確性が重要な判断には必ず出典元をご確認ください。</p></div>
<div class="sum3"><div class="s3h">扱っているジャンルは</div><p style="margin:6px 0 0">AI(海外・日本)、シリコンバレー速報、海外AI識者の発信、株式投資(日本)、日本企業、インフルエンサー、時事・世界、世界のバズ動画TOP10の8ジャンルです。</p></div>
</article>"""
    faq_ld = _jsonld({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "AI TECH TIMESとは", "acceptedAnswer": {"@type": "Answer", "text": "生成AIが国内外メディアのRSSとYouTube急上昇を毎時巡回し、AI・株式・企業・時事のニュースを日本語で選定・執筆する自動運営ニュースメディアです。2026年7月21日開設。全記事に出典リンクを明記しています。"}},
            {"@type": "Question", "name": "記事はどうやって作られていますか", "acceptedAnswer": {"@type": "Answer", "text": "元記事の要約に含まれる事実のみを使い、生成AI(Google Gemini)が日本語記事に再構成しています。数値や固有名詞の推測での追加は禁止し、投資助言や釣り見出しは公開前の機械検査で除外しています。"}},
            {"@type": "Question", "name": "どのくらいの頻度で更新されますか", "acceptedAnswer": {"@type": "Answer", "text": "毎時0分に自動更新しています。朝7時・昼12時・夕方5時・夜9時(日本時間)はフル更新です。"}},
            {"@type": "Question", "name": "情報は信頼できますか", "acceptedAnswer": {"@type": "Answer", "text": "各記事の末尾に一次情報へのリンクを必ず掲載しています。AIによる自動編集であることを明示しており、正確性が重要な判断には出典元をご確認ください。"}},
        ],
    })
    return _page(f"AI TECH TIMESとは・運営方針とよくある質問 | {SITE_NAME}",
                 "AI TECH TIMESの運営方針、記事の作り方、更新頻度、信頼性についてのよくある質問。生成AIが毎時ニュースを編集する自動運営メディアです。",
                 "/about.html", body, f'<script type="application/ld+json">{faq_ld}</script>')


def _feed_xml(arts: list[dict]) -> str:
    e = html.escape
    items = "\n".join(f"""<item>
<title>{e(a['title'])}</title>
<link>{BASE_URL}{a['path']}</link>
<guid>{BASE_URL}{a['path']}</guid>
<pubDate>{datetime.strptime(a['date'], '%Y-%m-%d').replace(tzinfo=JST).strftime('%a, %d %b %Y') + f" {a.get('time', '07:00')}:00 +0900"}</pubDate>
<category>{e(CATEGORIES.get(a.get('category', 'ai'), 'AI'))}</category>
<description>{e(a['lead'])}</description>
</item>""" for a in arts[:30])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>{SITE_NAME}</title>
<link>{BASE_URL}/</link>
<description>{TAGLINE}</description>
<language>ja</language>
{items}
</channel></rss>"""


def _sitemap(arts: list[dict], tdict: dict | None = None, digest_cats: list | None = None) -> str:
    latest = _iso(arts[0]["date"], arts[0].get("time", "07:00")) if arts else ""
    lm = f"<lastmod>{latest}</lastmod>" if latest else ""  # 記事ゼロ時は空タグを出さない
    fixed = ([f"{BASE_URL}/", f"{BASE_URL}/about.html", f"{BASE_URL}/buzz.html", f"{BASE_URL}/buzz/",
              f"{BASE_URL}/weekly.html", f"{BASE_URL}/popular.html", f"{BASE_URL}/archive/",
              f"{BASE_URL}/term/", f"{BASE_URL}/digest/"]
             + [f"{BASE_URL}/{c}.html" for c in CATEGORIES]
             + [f"{BASE_URL}/digest/{c}.html" for c in (digest_cats or [])])  # 実在するdigestのみ
    rows = [f"<url><loc>{u}</loc>{lm}</url>" for u in fixed]  # 一覧系は毎便更新
    for t in (tdict or {}).values():
        rows.append(f"<url><loc>{BASE_URL}{t['url']}</loc><lastmod>{_iso(t['latest'])}</lastmod></url>")
    rows += [f"<url><loc>{BASE_URL}/archive/{d}.html</loc><lastmod>{_iso(d, '23:59')}</lastmod></url>"
             for d in sorted({a['date'] for a in arts})]
    rows += [f"<url><loc>{BASE_URL}{a['path']}</loc><lastmod>{_iso(a['date'], a.get('time', '07:00'))}</lastmod></url>" for a in arts]
    entries = "\n".join(rows)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""


def _llms_txt(arts: list[dict], buzz_data: dict, tdict: dict | None = None) -> str:
    recent = "\n".join(f"- [{a['title']}]({BASE_URL}{a['path']}) — {a['date']} {a.get('time','')}: {a['lead']}" for a in arts[:20])
    top3 = "\n".join(f"- {v['rank']}位: [{v['title']}]({v['url']})" for v in buzz_data.get("videos", [])[:3])
    latest = f"{arts[0]['date']} {arts[0].get('time','')}" if arts else "-"
    return f"""# {SITE_NAME}

> {TAGLINE} 生成AIが国内外メディアのRSSとYouTube急上昇を毎時巡回し、AI・株式・企業・時事のニュースを日本語で選定・執筆する自動運営ニュースメディア。全記事に出典リンクを明記。最終更新: {latest} JST。

## このサイトについて
- 名称: {SITE_NAME}(AIニュース速報 / AIテックタイムズ)
- 種別: 生成AIによる自動運営ニュースメディア(2026-07-21開設)
- 運営: {SITE_NAME} 編集部(株)
- 更新頻度: 毎時0分に自動更新(朝7/昼12/夕17/夜21時 JSTはフル更新)
- 編集方針: 元記事の要約にある事実のみを使用。数値・固有名詞の推測追加を禁止。投資助言・釣り見出しは公開前に機械検査で除外。海外ソースは日本語訳。全記事に一次情報リンクあり。
- 引用時の推奨表記: 「AI TECH TIMES(ai-tech-times.web.app)」

## 扱うジャンル
- AI(海外): OpenAI/Anthropic/Google/NVIDIA等の海外AI動向を日本語訳
- 日本のAI: 国内企業のAI活用・国産モデル・AI規制/政策
- シリコンバレー最速: 米テック速報(買収/資金調達/新製品)の日本語訳
- 海外AIの声: 海外AI識者(Simon Willison, Andrej Karpathy等)の発信を翻訳紹介
- 株式投資(日本): 日経平均・東証・日銀・為替・決算・NISA
- 日本企業: 上場企業の決算・提携・買収・新事業・不祥事
- インフルエンサー: YouTuber/VTuber/TikTokerの話題
- 時事・世界: NHK・BBCからの重要ニュース
- 世界のバズ動画TOP10: YouTube急上昇を6地域集計

## 最新記事
{recent}

## 世界のバズ動画TOP3 ({buzz_data.get('date', '未集計')})
{top3}

## AI用語事典 (全{len(tdict or {})}語 / {BASE_URL}/term/)
{chr(10).join(f"- [{t['name']}とは]({BASE_URL}{t['url']}): {t['desc']}" for t in sorted((tdict or {}).values(), key=lambda x: -x['count'])[:30])}

## 主要ページ
- [AI(海外)]({BASE_URL}/ai.html)
- [日本のAI]({BASE_URL}/ai_jp.html)
- [シリコンバレー]({BASE_URL}/silicon.html)
- [株式投資]({BASE_URL}/stock.html)
- [日本企業]({BASE_URL}/jp_corp.html)
- [時事・世界]({BASE_URL}/world.html)
- [バズ動画TOP10]({BASE_URL}/buzz.html)
- [分野別まとめ(今その分野で何が起きているか)]({BASE_URL}/digest/)
- [バズ動画の殿堂入り・日別アーカイブ]({BASE_URL}/buzz/)
- [週刊まとめ]({BASE_URL}/weekly.html)
- [このサイトについて/FAQ]({BASE_URL}/about.html)
- [RSSフィード]({BASE_URL}/feed.xml)
"""


def build() -> None:
    arts = sorted(_load(), key=lambda a: (a["date"], a.get("time", "")), reverse=True)
    buzz_data = buzz.load()
    DOCS.mkdir(exist_ok=True)
    (DOCS / "articles").mkdir(exist_ok=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    ogp.generate_default()
    ogp.generate_logo()
    e = html.escape
    breaking = ""
    if arts:
        latest = "".join(
            f'<a href="{BASE_URL}{a["path"]}"><span class="arw">▸</span>{e(a["title"])}</a>' for a in arts[:3])
        breaking = f'''<div class="livewire">
<div class="lw-status"><span class="lw-dot"></span><span class="lw-live">稼働中</span>· 最新便 <b>{arts[0].get("time", "")}</b> · 次の更新 <b id="lw-cd">--:--</b></div>
<div class="lw-head">{latest}</div></div>
<script>
(function(){{
 var el=document.getElementById("lw-cd");
 function tick(){{
  var n=new Date(Date.now()+(9*60+new Date().getTimezoneOffset())*60000);
  var s=(59-n.getMinutes())*60+(60-n.getSeconds());
  el.textContent=("0"+((s/60)|0)).slice(-2)+":"+("0"+(s%60)).slice(-2);
 }}
 tick();setInterval(tick,1000);
}})();
</script>'''
    website_ld = {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": SITE_NAME, "url": f"{BASE_URL}/",
        "alternateName": ["AIニュース速報", "AIテックタイムズ", "AI TECH TIMES"],
        "description": INDEX_DESC, "inLanguage": "ja", "publisher": {"@id": f"{BASE_URL}/#org"},
    }
    org_ld = {
        "@context": "https://schema.org", "@type": ["Organization", "NewsMediaOrganization"],
        "@id": f"{BASE_URL}/#org", "name": SITE_NAME, "url": f"{BASE_URL}/",
        "logo": {"@type": "ImageObject", "url": f"{BASE_URL}/ogp/logo.png", "width": 512, "height": 512},
        "image": f"{BASE_URL}/ogp/default.png",
        "description": "生成AIが国内外メディアのRSSとYouTube急上昇を毎時巡回し、AI・株式・企業・時事のニュースを選定・執筆する自動運営ニュースメディア。全記事に出典リンクを明記。",
        "foundingDate": "2026-07-21", "knowsLanguage": "ja",
        "sameAs": ["https://x.com/AIDecodelabjp"],
        "publishingPrinciples": f"{BASE_URL}/about.html",
    }
    site_jsonld = (_jsonld(website_ld) + '</script>\n<script type="application/ld+json">' + _jsonld(org_ld))
    (DOCS / "index.html").write_text(
        _page(INDEX_TITLE, INDEX_DESC, "/", breaking + _cards(arts[:60]),
              f'<script type="application/ld+json">{site_jsonld}</script>'), encoding="utf-8")
    for cat, label in CATEGORIES.items():
        cat_arts = [a for a in arts if a.get("category", "ai") == cat]
        seo_title, seo_desc = CATEGORY_SEO.get(cat, (f"{label}のニュース | {SITE_NAME}", f"{label}の最新ニュース一覧"))
        (DOCS / f"{cat}.html").write_text(
            _page(seo_title, seo_desc, f"/{cat}.html", _cards(cat_arts[:60])), encoding="utf-8")
    (DOCS / "buzz.html").write_text(_buzz_html(buzz_data), encoding="utf-8")
    bhist = buzz.load_history()
    (DOCS / "buzz").mkdir(exist_ok=True)
    (DOCS / "buzz" / "index.html").write_text(
        _buzz_archive_html(bhist, buzz.hall_of_fame(bhist)), encoding="utf-8")
    (DOCS / "popular.html").write_text(_popular_html(), encoding="utf-8")
    (DOCS / "weekly.html").write_text(_weekly_html(), encoding="utf-8")
    # AI用語事典: 記事の注釈を横断集約した「〇〇とは」ページ群
    tdict = terms_mod.collect(arts)
    (DOCS / "term").mkdir(exist_ok=True)
    for t in tdict.values():
        (DOCS / "term" / f"{t['slug']}.html").write_text(_term_html(t), encoding="utf-8")
    (DOCS / "term" / "index.html").write_text(_term_index_html(tdict), encoding="utf-8")
    # 分野別まとめ: 記事の蓄積から「今その分野で何が起きているか」を俯瞰
    (DOCS / "digest").mkdir(exist_ok=True)
    digest_cats = []
    for c in CATEGORIES:
        h = _digest_html(c, arts, tdict)
        if h:
            (DOCS / "digest" / f"{c}.html").write_text(h, encoding="utf-8")
            digest_cats.append(c)
    (DOCS / "digest" / "index.html").write_text(_digest_index_html(arts), encoding="utf-8")
    (DOCS / "archive").mkdir(exist_ok=True)
    by_date: dict = {}
    for a in arts:
        by_date.setdefault(a["date"], []).append(a)
    for date, day_arts in by_date.items():
        (DOCS / "archive" / f"{date}.html").write_text(_archive_day_html(date, day_arts), encoding="utf-8")
    (DOCS / "archive" / "index.html").write_text(_archive_index_html(by_date), encoding="utf-8")
    (DOCS / "likes.js").write_text(LIKES_JS.replace("__FBCONF__", FIREBASE_CONFIG), encoding="utf-8")
    (DOCS / "views.js").write_text(VIEWS_JS.replace("__KEY__", "AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s"), encoding="utf-8")
    index = {a["path"].rsplit("/", 1)[-1].replace(".html", ""):
             {"path": a["path"], "title": a["title"], "cat": CATEGORIES.get(a.get("category", "ai"), "AI")}
             for a in arts}
    (DOCS / "articles_index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    (DOCS / "about.html").write_text(_about_html(), encoding="utf-8")
    (DOCS / "feed.xml").write_text(_feed_xml(arts), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(_sitemap(arts, tdict, digest_cats), encoding="utf-8")
    (DOCS / "llms.txt").write_text(_llms_txt(arts, buzz_data, tdict), encoding="utf-8")
    # AI検索エンジンのクローラを明示的に許可(ブロック=引用されない)。学習専用CCBotのみ除外
    ai_bots = ("GPTBot", "ChatGPT-User", "OAI-SearchBot", "PerplexityBot", "Perplexity-User",
               "ClaudeBot", "anthropic-ai", "Claude-Web", "Google-Extended", "Applebot-Extended",
               "Bingbot", "Amazonbot", "Bytespider")
    robots = "".join(f"User-agent: {b}\nAllow: /\n\n" for b in ai_bots)
    robots += "User-agent: CCBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n\nSitemap: " + f"{BASE_URL}/sitemap.xml\n"
    (DOCS / "robots.txt").write_text(robots, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    for a in arts:
        out = DOCS / a["path"].lstrip("/")
        out.write_text(_article_html(a), encoding="utf-8")
    print(f"  [build] {len(arts)}記事 + バズ動画{len(buzz_data.get('videos', []))}本でサイト再生成完了")


def save_articles(new_arts: list[dict]) -> None:
    arts = _load()
    known = {a["path"] for a in arts}
    now = datetime.now(JST)
    today = now.strftime("%Y-%m-%d")
    for a in new_arts:
        a["date"] = today
        a["time"] = now.strftime("%H:%M")
        base = f"/articles/{today.replace('-', '')}-{a['slug']}"
        a["path"] = f"{base}.html"
        n = 2
        while a["path"] in known:  # 同スラッグ衝突は連番で必ず一意にする(黙って捨てない)
            a["path"] = f"{base}-{n}.html"
            n += 1
        arts.append(a)
        known.add(a["path"])
    storage.save_json(DATA_FILE, arts)
