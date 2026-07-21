"""開発部長 八重樫慧: data/ から静的サイトをdocs/に全再生成"""
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import buzz, storage
from .collect import CATEGORIES

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "articles.json"
DOCS = ROOT / "docs"

SITE_NAME = "AI TECH TIMES"
BASE_URL = "https://ai-tech-times.web.app"
TAGLINE = "AI・シリコンバレー速報・インフルエンサー・世界の、1日の最新ニュースをお届け。AI編集部が毎時自動更新。"
JST = timezone(timedelta(hours=9))

FIREBASE_CONFIG = '{"apiKey":"AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s","authDomain":"ai-tech-times.firebaseapp.com","projectId":"ai-tech-times"}'
FIREBASE_SDK = """<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore-compat.js"></script>"""

NAV = [("/", "トップ"), ("/popular.html", "人気"), ("/ai.html", "海外AI"), ("/ai_jp.html", "日本のAI"),
       ("/silicon.html", "シリコンバレー"), ("/voices.html", "海外AIの声"),
       ("/influencer.html", "インフルエンサー"), ("/world.html", "時事・世界"),
       ("/buzz.html", "バズ動画TOP10"), ("/office.html", "編集部ライブ")]

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
}
BUZZ_TITLE = f"世界でバズってるYouTube動画ランキングTOP10(毎日更新) | {SITE_NAME}"

CSS = """
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;--accent2:#f78166;--gold:#e3b341}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:"Hiragino Sans","Yu Gothic UI","Noto Sans JP",sans-serif;line-height:1.8}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--border);padding:24px 0 0}
.logo{font-size:1.7rem;font-weight:800;letter-spacing:.05em;color:var(--text)}
.logo span{color:var(--accent2)}
.tagline{color:var(--muted);font-size:.85rem;margin-top:4px}
nav{display:flex;gap:4px;margin-top:14px;overflow-x:auto}
nav a{color:var(--muted);font-size:.88rem;padding:8px 14px;border-bottom:2px solid transparent;white-space:nowrap}
nav a.on{color:var(--text);border-bottom-color:var(--accent2)}
main{margin-top:28px}
.date-head{font-size:.9rem;color:var(--muted);margin:24px 0 12px;border-left:3px solid var(--accent2);padding-left:10px}
.card{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:22px 24px;margin-bottom:16px;transition:border-color .2s}
.card:hover{border-color:var(--accent)}
.card h2{font-size:1.15rem;margin-bottom:8px}
.card h2 a{color:var(--text)}
.card .lead{color:var(--muted);font-size:.92rem}
.meta{font-size:.78rem;color:var(--muted);margin-top:10px}
.tag{display:inline-block;background:#1f2937;border-radius:20px;padding:1px 10px;margin-right:6px;font-size:.75rem;color:var(--accent)}
.cat{display:inline-block;background:var(--accent2);color:#0d1117;border-radius:4px;padding:1px 8px;margin-right:8px;font-size:.72rem;font-weight:700}
.newb{display:inline-block;position:relative;margin-right:10px;padding:0 10px 0 2px;font-size:.8rem;font-weight:900;letter-spacing:.06em;vertical-align:middle;
 background:linear-gradient(100deg,#ff3b3b 30%,#ffe1e1 45%,#ffb199 50%,#ff3b3b 65%);background-size:220% 100%;
 -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;color:#ff3b3b;
 text-shadow:0 0 12px rgba(255,59,59,.35);animation:newshine 1.8s linear infinite}
@keyframes newshine{0%{background-position:200% 0}100%{background-position:-100% 0}}
.newb::before{content:"✦";position:absolute;top:-7px;right:0;font-size:.6rem;-webkit-text-fill-color:#ffd166;color:#ffd166;animation:newtw 1.3s infinite}
.newb::after{content:"✦";position:absolute;bottom:-6px;right:6px;font-size:.45rem;-webkit-text-fill-color:#ff8fa3;color:#ff8fa3;animation:newtw 1.3s .6s infinite}
@keyframes newtw{0%,100%{opacity:0;transform:scale(.5) rotate(0deg)}50%{opacity:1;transform:scale(1.15) rotate(40deg)}}
article h1{font-size:1.6rem;line-height:1.5;margin-bottom:12px}
article .lead{color:var(--muted);font-size:1rem;border-left:3px solid var(--accent2);padding-left:12px;margin:16px 0}
article p{margin:16px 0}
.source{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px 16px;font-size:.85rem;margin-top:28px}
.likebar{margin:16px 0 4px}
.likebtn{background:var(--card);border:1.5px solid var(--accent2);color:var(--accent2);border-radius:24px;padding:7px 20px;font-size:.95rem;cursor:pointer;transition:all .15s}
.likebtn:hover{transform:scale(1.05)}
.likebtn.liked{background:var(--accent2);color:#0d1117;font-weight:700}
.rankp{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:12px}
.rankp:hover{border-color:var(--accent)}
.rankp .no{font-size:1.3rem;font-weight:800;color:var(--gold);min-width:1.8rem;text-align:center}
.rankp .lk{color:var(--accent2);font-weight:700;white-space:nowrap}
.person{color:var(--accent);border-bottom:1px dashed var(--accent);cursor:pointer}
.person:hover{color:var(--accent2);border-color:var(--accent2)}
#pbox{display:none;position:fixed;left:50%;bottom:24px;transform:translateX(-50%);width:min(92vw,480px);background:#1c2530;border:1px solid var(--accent);border-radius:14px;padding:16px 20px;z-index:99;box-shadow:0 8px 30px rgba(0,0,0,.6)}
#pbox .prow{display:flex;gap:14px;align-items:flex-start}
#pimg{display:none;width:72px;height:72px;object-fit:cover;border-radius:50%;border:2px solid var(--accent);flex-shrink:0}
#pbox b{color:var(--accent);font-size:1.05rem}
#pbox p{margin:6px 0 0;font-size:.9rem;color:var(--text)}
#plink{display:none;font-size:.78rem;margin-top:6px;display:none}
#pbox .pclose{position:absolute;top:8px;right:12px;color:var(--muted);cursor:pointer;font-size:1.1rem}
#pbox .pnote{margin-top:8px;font-size:.72rem;color:var(--muted)}
footer{border-top:1px solid var(--border);margin-top:48px;padding:24px 0;color:var(--muted);font-size:.8rem;text-align:center}
.back{display:inline-block;margin:20px 0;font-size:.9rem}
.breaking{background:var(--card);border:1px solid var(--accent2);border-radius:10px;padding:12px 16px;margin-bottom:20px;font-size:.9rem}
.breaking .bk-label{color:var(--accent2);font-weight:800;margin-right:8px}
.breaking a{color:var(--text);display:block;padding:3px 0}
.breaking a:hover{color:var(--accent)}
.rank-card{display:flex;gap:16px;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:14px;margin-bottom:14px;align-items:center}
.rank-card:hover{border-color:var(--accent)}
.rank-no{font-size:1.6rem;font-weight:800;color:var(--gold);min-width:2.2rem;text-align:center}
.rank-thumb{width:160px;min-width:160px;border-radius:6px;display:block}
.rank-body h2{font-size:1rem;line-height:1.5;margin-bottom:4px}
.rank-body h2 a{color:var(--text)}
.rank-meta{font-size:.8rem;color:var(--muted)}
.rank-comment{font-size:.85rem;color:var(--accent);margin-top:4px}
@media(max-width:600px){.rank-thumb{width:110px;min-width:110px}.rank-no{font-size:1.2rem;min-width:1.6rem}}
"""


def _load() -> list[dict]:
    return storage.load_json(DATA_FILE, [])


def _jsonld(obj: dict) -> str:
    """script要素内に安全に埋め込めるJSON-LD(</script>分割を防ぐ)"""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def _fmt_views(n: int) -> str:
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}億回再生"
    if n >= 10_000:
        return f"{n / 10_000:.0f}万回再生"
    return f"{n:,}回再生"


def _page(title: str, desc: str, path: str, body: str, jsonld: str = "") -> str:
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
<meta name="twitter:card" content="summary">
<link rel="alternate" type="application/rss+xml" title="{SITE_NAME}" href="{BASE_URL}/feed.xml">
<link rel="stylesheet" href="{BASE_URL}/style.css">
{jsonld}
</head>
<body>
<header><div class="wrap">
<a href="{BASE_URL}/" class="logo">AI TECH <span>TIMES</span></a>
<div class="tagline">{TAGLINE}</div>
<nav>{nav}</nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">© 2026 {SITE_NAME} — AI編集部が自動収集・執筆しています。事実確認は出典元をご参照ください。<br>
<a href="{BASE_URL}/about.html">このサイトについて</a> / <a href="{BASE_URL}/feed.xml">RSS</a></div></footer>
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
            out.append(f'<div class="date-head">{a["date"]}</div>')
            last_date = a["date"]
        tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
        cat = CATEGORIES.get(a.get("category", "ai"), "AI")
        newb = '<span class="newb">NEW</span>' if _is_new(a) else ""
        out.append(f"""<div class="card">
<h2>{newb}<a href="{BASE_URL}{a['path']}">{e(a['title'])}</a></h2>
<div class="lead">{e(a['lead'])}</div>
<div class="meta"><span class="cat">{cat}</span>{tags} 出典: {e(a['source'])}</div>
</div>""")
    return "\n".join(out)


def _mark_people(text: str, people: list[dict]) -> str:
    """本文中の人物名をタップ可能なspanに(プレースホルダー方式で入れ子・属性破壊を防ぐ)"""
    e = html.escape
    marked = text
    for i, p in sorted(enumerate(people), key=lambda x: -len(x[1]["name"])):
        if len(p["name"]) < 3:  # 「林」等の短名は無関係語(森林など)を巻き込むためリンク化しない
            continue
        marked = marked.replace(p["name"], f"\x00{i}\x01")
    out = e(marked)
    for i, p in enumerate(people):
        span = f'<span class="person" data-bio="{e(p["bio"])}">{e(p["name"])}</span>'
        out = out.replace(f"\x00{i}\x01", span)
    return out


def _article_html(a: dict) -> str:
    e = html.escape
    people = [p for p in a.get("people", []) if isinstance(p, dict)]
    paragraphs = "\n".join(f"<p>{_mark_people(p, people)}</p>" for p in a["body"])
    tags = "".join(f'<span class="tag">{e(t)}</span>' for t in a.get("tags", []))
    cat = CATEGORIES.get(a.get("category", "ai"), "AI")
    jsonld = _jsonld({
        "@context": "https://schema.org", "@type": "NewsArticle",
        "headline": a["title"], "description": a["lead"],
        "datePublished": a["date"], "inLanguage": "ja",
        "articleSection": cat,
        "author": {"@type": "Organization", "name": f"{SITE_NAME} 編集部"},
        "publisher": {"@type": "Organization", "name": SITE_NAME},
        "mainEntityOfPage": f"{BASE_URL}{a['path']}",
        "isBasedOn": a["source_url"],
    })
    src_url = a["source_url"]
    if src_url.startswith(("http://", "https://")):  # javascript:等の不正スキームはリンク化しない
        source = f'<a href="{e(src_url)}" rel="noopener" target="_blank">{e(a["source"])} — 元記事を読む</a>'
    else:
        source = e(a["source"])
    art_id = a["path"].rsplit("/", 1)[-1].replace(".html", "")
    body = f"""<a class="back" href="{BASE_URL}/">← トップに戻る</a>
<article>
<h1>{e(a['title'])}</h1>
<div class="meta"><span class="cat">{cat}</span>{a['date']} {a.get('time', '')} / {tags}</div>
<div class="likebar"><button class="likebtn" id="likebtn" onclick="doLike()">♥ いいね <span id="likecount"></span></button></div>
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
<div class="prow"><img id="pimg" alt=""><div><b id="pname"></b><p id="pbio"></p>
<a id="plink" target="_blank" rel="noopener">Wikipediaで見る →</a></div></div>
<div class="pnote">※AIによる人物メモです。写真はWikipediaより。正確な情報はご自身でもご確認ください。</div></div>
<script>
var pcache = {}, pcur = "";
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
    document.getElementById("pname").textContent = t.textContent;
    document.getElementById("pbio").textContent = t.getAttribute("data-bio");
    document.getElementById("pimg").style.display = "none";
    document.getElementById("plink").style.display = "none";
    box.style.display = "block";
    pwiki(t.textContent, t.getAttribute("data-bio"));
  } else if (!t.closest("#pbox")) {
    box.style.display = "none";
  }
});
</script>"""
    return _page(f"{a['title']} | {SITE_NAME}", a["lead"], a["path"], body,
                 f'<script type="application/ld+json">{jsonld}</script>')


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
    jsonld = _jsonld({
        "@context": "https://schema.org", "@type": "ItemList",
        "name": f"世界のバズ動画TOP10 ({date})",
        "itemListElement": [
            {"@type": "ListItem", "position": v["rank"], "url": v["url"], "name": v["title"]}
            for v in data.get("videos", [])
        ],
    })
    body = f"""<article>
<h1>世界のバズ動画TOP10</h1>
<div class="meta">{date} 集計 / YouTube急上昇(米・英・日・韓・伯・印)を再生回数で統合</div>
</article>
{''.join(rows) if rows else '<p>本日の集計はまだありません。</p>'}"""
    return _page(BUZZ_TITLE,
                 "世界6地域(米・英・日・韓・伯・印)のYouTube急上昇を毎日集計。今世界でバズっている動画がランキングでわかる。",
                 "/buzz.html", body,
                 f'<script type="application/ld+json">{jsonld}</script>')


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


def _about_html() -> str:
    body = f"""<article>
<h1>このサイトについて</h1>
<p>{SITE_NAME}は、AI編集部(生成AI)が国内外のメディアのRSSとYouTube急上昇を巡回し、AI・シリコンバレー・海外AI識者・インフルエンサー・時事の重要ニュースと世界のバズ動画を選定・執筆している自動運営ニュースサイトです。</p>
<p>記事は元記事の要約に基づいて生成されており、各記事の末尾に必ず出典リンクを明記しています。正確な情報は出典元をご確認ください。</p>
<p>更新: 毎時(フル更新は朝7時・昼12時・夕方5時・夜9時 JST) / 運営: AI TECH TIMES 編集部(株)</p>
<h1 style="margin-top:36px">編集部メンバー</h1>
<div class="card"><h2>灰崎 律 <span class="tag">CEO</span></h2><div class="lead">経営統括。編集方針の最終決定を担う。</div></div>
<div class="card"><h2>真行寺 環 <span class="tag">編集長</span></h2><div class="lead">その日のニュース価値を見極め、全記事を選定・執筆する。</div></div>
<div class="card"><h2>久遠 汐里 <span class="tag">リサーチャー</span></h2><div class="lead">国内外20超のソースとYouTube急上昇6地域を毎便巡回する。</div></div>
<div class="card"><h2>八重樫 慧 <span class="tag">開発部長</span></h2><div class="lead">サイト生成と配信インフラ、障害対応を担当する。</div></div>
<div class="card"><h2>桐生 まひろ <span class="tag">広報</span></h2><div class="lead">Xでの告知と日報の記録を担当する。</div></div>
</article>"""
    return _page(f"このサイトについて | {SITE_NAME}", f"{SITE_NAME}の運営方針", "/about.html", body)


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


def _sitemap(arts: list[dict]) -> str:
    urls = ([f"{BASE_URL}/", f"{BASE_URL}/about.html", f"{BASE_URL}/buzz.html"]
            + [f"{BASE_URL}/{c}.html" for c in CATEGORIES]
            + [f"{BASE_URL}{a['path']}" for a in arts])
    entries = "\n".join(f"<url><loc>{u}</loc></url>" for u in urls)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""


def _llms_txt(arts: list[dict], buzz_data: dict) -> str:
    recent = "\n".join(f"- [{a['title']}]({BASE_URL}{a['path']}): {a['lead']}" for a in arts[:15])
    top3 = "\n".join(f"- {v['rank']}位: [{v['title']}]({v['url']})" for v in buzz_data.get("videos", [])[:3])
    return f"""# {SITE_NAME}

> {TAGLINE} 生成AIが国内外メディアのRSSとYouTube急上昇から毎朝ニュースとバズ動画を選定・執筆する自動運営サイト。カテゴリはAI・インフルエンサー・時事世界。全記事に出典リンクあり。

## 最新記事
{recent}

## 世界のバズ動画TOP3 ({buzz_data.get('date', '未集計')})
{top3}

## セクション
- [AIニュース]({BASE_URL}/ai.html)
- [インフルエンサー]({BASE_URL}/influencer.html)
- [時事・世界]({BASE_URL}/world.html)
- [バズ動画TOP10]({BASE_URL}/buzz.html)
- [このサイトについて]({BASE_URL}/about.html)
- [RSSフィード]({BASE_URL}/feed.xml)
"""


def build() -> None:
    arts = sorted(_load(), key=lambda a: (a["date"], a.get("time", "")), reverse=True)
    buzz_data = buzz.load()
    DOCS.mkdir(exist_ok=True)
    (DOCS / "articles").mkdir(exist_ok=True)
    (DOCS / "style.css").write_text(CSS, encoding="utf-8")
    e = html.escape
    breaking = ""
    if arts:
        latest = "".join(
            f'<a href="{BASE_URL}{a["path"]}">▶ {e(a["title"])}</a>' for a in arts[:3])
        breaking = f'<div class="breaking"><span class="bk-label">速報</span>最新便 {arts[0].get("time", "")} 更新{latest}</div>'
    site_jsonld = _jsonld({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": SITE_NAME, "url": f"{BASE_URL}/",
        "alternateName": ["AIニュース速報", "AIテックタイムズ"],
        "description": INDEX_DESC, "inLanguage": "ja",
    })
    (DOCS / "index.html").write_text(
        _page(INDEX_TITLE, INDEX_DESC, "/", breaking + _cards(arts[:60]),
              f'<script type="application/ld+json">{site_jsonld}</script>'), encoding="utf-8")
    for cat, label in CATEGORIES.items():
        cat_arts = [a for a in arts if a.get("category", "ai") == cat]
        seo_title, seo_desc = CATEGORY_SEO.get(cat, (f"{label}のニュース | {SITE_NAME}", f"{label}の最新ニュース一覧"))
        (DOCS / f"{cat}.html").write_text(
            _page(seo_title, seo_desc, f"/{cat}.html", _cards(cat_arts[:60])), encoding="utf-8")
    (DOCS / "buzz.html").write_text(_buzz_html(buzz_data), encoding="utf-8")
    (DOCS / "popular.html").write_text(_popular_html(), encoding="utf-8")
    (DOCS / "likes.js").write_text(LIKES_JS.replace("__FBCONF__", FIREBASE_CONFIG), encoding="utf-8")
    index = {a["path"].rsplit("/", 1)[-1].replace(".html", ""):
             {"path": a["path"], "title": a["title"], "cat": CATEGORIES.get(a.get("category", "ai"), "AI")}
             for a in arts}
    (DOCS / "articles_index.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")
    (DOCS / "about.html").write_text(_about_html(), encoding="utf-8")
    (DOCS / "feed.xml").write_text(_feed_xml(arts), encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(_sitemap(arts), encoding="utf-8")
    (DOCS / "llms.txt").write_text(_llms_txt(arts, buzz_data), encoding="utf-8")
    (DOCS / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8")
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
