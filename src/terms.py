"""編集長 真行寺環: AI用語事典(term/)の構築

記事に付与した注釈(terms/people)を横断集約し、用語ごとの解説ページを作る。
「〇〇とは」検索に応える当社の資産。定義は最も詳しい注釈を採用し、
その用語が登場した記事(=当社の報道履歴)を関連づける。
"""
import re
import unicodedata
import urllib.parse
from collections import defaultdict

# 表記ゆれの統合(左を右に寄せる)。日本語表記と英語表記が混在するため
ALIAS = {
    "アルファベット": "Alphabet",
    "グーグル": "Google",
    "アップル": "Apple",
    "マイクロソフト": "Microsoft",
    "エヌビディア": "NVIDIA",
    "テスラ": "Tesla",
    "アマゾン": "Amazon",
    "メタ": "Meta",
    "オープンAI": "OpenAI",
    "トランプ": "トランプ大統領",
    "ドナルド・トランプ": "トランプ大統領",
}

# 事典に載せない一般語(固有性が低く解説価値がないもの)
SKIP = {"AI", "ai", "IT", "SNS", "米国", "日本", "中国"}


def canonical(name: str) -> str:
    n = unicodedata.normalize("NFKC", name).strip()
    n = re.sub(r"(氏|さん)$", "", n)
    return ALIAS.get(n, n)


def slugify(name: str) -> str:
    """URLに使える識別子。英数語はハイフン形式、日本語名はそのまま(URLで意味が伝わる方がAI/人間に有利)"""
    n = unicodedata.normalize("NFKC", name).lower()
    s = re.sub(r"[^a-z0-9]+", "-", n).strip("-")
    if len(s) >= 2:
        return s[:60]
    # 日本語のみの語: ファイル名に使えない文字だけ除去して日本語のまま使う
    jp = re.sub(r'[\\/:*?"<>|#%&{}\s]+', "", unicodedata.normalize("NFKC", name))
    return jp[:40] if jp else "term-" + name.encode("utf-8").hex()[:16]


def url_slug(slug: str) -> str:
    """HTML/サイトマップに書くときのURLエンコード済みslug(日本語slug対応)"""
    return urllib.parse.quote(slug, safe="-_.")


def collect(articles: list[dict]) -> dict:
    """{canonical_name: {kind, desc, aliases, articles:[...]}} を返す"""
    bucket: dict = defaultdict(lambda: {"kind": "", "descs": [], "aliases": set(), "articles": []})
    for a in articles:
        seen = set()
        for t in a.get("terms", []):
            if not isinstance(t, dict):
                continue
            raw = str(t.get("name", "")).strip()
            if not raw or raw in SKIP:
                continue
            key = canonical(raw)
            if key in seen:
                continue
            seen.add(key)
            b = bucket[key]
            b["kind"] = b["kind"] or t.get("type", "company")
            b["descs"].append(str(t.get("desc", "")).strip())
            b["aliases"].add(raw)
            b["articles"].append(a)
        for p in a.get("people", []):
            if not isinstance(p, dict):
                continue
            raw = str(p.get("name", "")).strip()
            if not raw or raw in SKIP:
                continue
            key = canonical(raw)
            if key in seen:
                continue
            seen.add(key)
            b = bucket[key]
            b["kind"] = b["kind"] or "person"
            b["descs"].append(str(p.get("bio", "")).strip())
            b["aliases"].add(raw)
            b["articles"].append(a)

    out = {}
    for name, b in bucket.items():
        descs = [d for d in b["descs"] if d]
        if not descs:
            continue
        # 定義は最頻出のものを優先し、同数なら詳しいものを採用
        freq: dict = defaultdict(int)
        for d in descs:
            freq[d] += 1
        best = sorted(descs, key=lambda d: (-freq[d], -len(d)))[0]
        arts = sorted(b["articles"], key=lambda a: (a["date"], a.get("time", "")), reverse=True)
        out[name] = {
            "name": name,
            "kind": b["kind"] or "company",
            "desc": best,
            "aliases": sorted(x for x in b["aliases"] if x != name),
            "articles": arts,
            "count": len(arts),
            "slug": slugify(name),
            "url": f"/term/{url_slug(slugify(name))}.html",  # HTML/sitemapはこれを使う
            "latest": arts[0]["date"] if arts else "",
        }
    return out
