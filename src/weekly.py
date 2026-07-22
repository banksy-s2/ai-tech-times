"""編集長 真行寺環: 週刊まとめ「今週のTOP10」(毎週月曜のフル便で自動発行、SEO資産)"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import storage
from .collect import CATEGORIES

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "weekly.json"
JST = timezone(timedelta(hours=9))


def load() -> dict:
    return storage.load_json(DATA_FILE, {})


def generate(articles: list[dict]) -> bool:
    """直近7日の記事からTOP10を選定して保存。候補不足ならスキップ"""
    from . import editor  # 循環import回避
    now = datetime.now(JST)
    week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    pool = [a for a in articles if a["date"] >= week_ago]
    if len(pool) < 10:
        print("  [weekly] 記事不足のためスキップ")
        return False
    listing = "\n".join(
        f"{i}: [{CATEGORIES.get(a.get('category', ''), '')}] {a['title']} — {a['lead'][:60]}"
        for i, a in enumerate(pool))
    prompt = f"""あなたはニュースサイトの編集長です。以下は今週掲載した記事です。「今週を振り返るのに欠かせない重要ニュースTOP10」を重要度順に選び、それぞれに一言解説(25字以内、事実のみ)を付けてください。同じ話題は1本まで。

{listing}

JSON配列のみ出力(重要度順に10要素): [{{"index": 数値, "comment": "一言解説"}}]"""
    data = editor._parse_json(editor._gemini(prompt))
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    items = []
    for p in data[:10]:
        i = p.get("index", -1) if isinstance(p, dict) else -1
        if 0 <= i < len(pool):
            a = pool[i]
            items.append({"path": a["path"], "title": a["title"],
                          "cat": CATEGORIES.get(a.get("category", ""), ""),
                          "comment": str(p.get("comment", "")).strip()[:40]})
    if len(items) < 5:
        print("  [weekly] 選定結果が不足のためスキップ")
        return False
    storage.save_json(DATA_FILE, {
        "week_of": now.strftime("%Y-%m-%d"),
        "range": f"{week_ago} 〜 {now.strftime('%Y-%m-%d')}",
        "items": items,
    })
    print(f"  [weekly] 週刊TOP10を発行({len(items)}本)")
    return True
