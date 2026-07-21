"""編集長 真行寺環: Gemini(無料枠)でネタ選定と記事執筆(REST直叩き・依存ゼロ)"""
import json
import os
import re
import time
import urllib.request

MODEL = "gemini-flash-latest"  # 無料枠で動く唯一のモデル(2.0-flashは枠0で429)
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

DAILY_PICKS = 3


def _gemini(prompt: str, retries: int = 3) -> str:
    key = os.environ["GEMINI_API_KEY"]
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}?key={key}", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if attempt == retries - 1:
                raise
            wait = 20 * (attempt + 1)
            print(f"  [editor] Gemini失敗({e})、{wait}秒後にリトライ")
            time.sleep(wait)


def _parse_json(text: str):
    """最初に見つかった完全なJSON値を取り出す(前後の余計なテキストや2個目のJSONを無視)"""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue
    return json.loads(text)


def select(candidates: list[dict]) -> list[dict]:
    """候補からトップ3を選定。話題の重複を避け、ニュース価値の高い順"""
    listing = "\n".join(
        f"{i}: [{c['source']}] {c['title']} — {c['summary'][:150]}"
        for i, c in enumerate(candidates))
    prompt = f"""あなたはAIニュースサイトの編集長です。以下の候補記事から、日本の読者にとってニュース価値が最も高い{DAILY_PICKS}本を選んでください。

ルール:
- 同じ話題(同じ発表を扱った記事)は1本だけ選ぶ
- 大手AI企業の新モデル/新製品発表、業界に影響する出来事を優先
- 単なるハウツー記事や宣伝は避ける

候補:
{listing}

JSON配列のみ出力: [{{"index": 数値, "reason": "選定理由1文"}}]"""
    data = _parse_json(_gemini(prompt))
    if isinstance(data, dict):  # {"picks": [...]} 形式で返るケース
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    picks = data[:DAILY_PICKS]
    return [candidates[p["index"]] for p in picks if 0 <= p.get("index", -1) < len(candidates)]


def write_article(item: dict) -> dict:
    """1本の候補を日本語記事に。元記事の要約にある事実のみ使用"""
    prompt = f"""あなたはAIニュースサイト「AI TECH TIMES」の記者です。以下の元記事情報だけを使って、日本語のニュース記事を書いてください。

元記事:
- 出典: {item['source']}
- タイトル: {item['title']}
- 要約: {item['summary']}
- URL: {item['url']}

厳守ルール:
- 上記の要約に書かれている事実だけを使う。数値・固有名詞・日付を推測で追加しない
- 要約が薄い場合は、一般に知られている背景(企業の説明など)を1〜2文だけ補ってよいが、新事実は作らない
- 本文は500〜800字、です・ます調
- 見出しは30字以内でキャッチーに

JSONのみ出力:
{{"title": "日本語見出し", "lead": "1〜2文のリード文", "body": ["段落1", "段落2", "段落3"], "tags": ["タグ1", "タグ2", "タグ3"], "slug": "english-slug-with-hyphens"}}"""
    art = _parse_json(_gemini(prompt))
    art["slug"] = re.sub(r"[^a-z0-9-]", "", art.get("slug", "news").lower())[:60] or "news"
    art["source"] = item["source"]
    art["source_url"] = item["url"]
    return art
