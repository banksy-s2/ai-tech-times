"""広報 桐生まひろ(兼務): 各便の日報を company/reports/ に自動記録"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import storage
from .collect import CATEGORIES

REPORTS = Path(__file__).resolve().parent.parent / "company" / "reports"
STATUS_FILE = Path(__file__).resolve().parent.parent / "docs" / "status.json"
JST = timezone(timedelta(hours=9))


def today_views() -> int | None:
    """自作カウンター(Firestore views/YYYYMMDD)から今日の閲覧数を取得"""
    import json as _json
    import urllib.request
    d = datetime.now(JST).strftime("%Y%m%d")
    url = (f"https://firestore.googleapis.com/v1/projects/ai-tech-times/databases/(default)/documents/views/{d}"
           f"?key=AIzaSyC3gYixsTTOb8TGgLwBEt7UplwClE_v00s&mask.fieldPaths=total")
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return int(_json.loads(r.read())["fields"]["total"]["integerValue"])
    except Exception:
        return None


def write_status(mode: str, articles: list[dict], buzz_top: dict | None, notes: list[str]) -> None:
    """編集部ライブ(office.html)が読む最新便ステータス"""
    storage.save_json(STATUS_FILE, {
        "updated": datetime.now(JST).strftime("%Y-%m-%d %H:%M"),
        "mode": mode,
        "articles": [{"title": a["title"], "path": a["path"],
                      "cat": CATEGORIES.get(a.get("category", "?"), "?")} for a in articles],
        "buzz_top": {"title": buzz_top["title"], "url": buzz_top["url"]} if buzz_top else None,
        "notes": notes,
        "pv_today": today_views(),
    })


def write(articles: list[dict], buzz_top: dict | None, notes: list[str]) -> None:
    now = datetime.now(JST)
    path = REPORTS / f"{now.strftime('%Y-%m-%d')}.md"
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# 日報 {now.strftime('%Y-%m-%d')}\n", encoding="utf-8")
    cats = Counter(a.get("category", "?") for a in articles)
    breakdown = " / ".join(f"{CATEGORIES.get(c, c)}{n}本" for c, n in cats.items()) or "なし"
    lines = [f"\n## {now.strftime('%H:%M')}便", f"- 掲載: {len(articles)}本({breakdown})"]
    for a in articles:
        lines.append(f"  - [{CATEGORIES.get(a.get('category', '?'), '?')}] {a['title']}")
    if buzz_top:
        lines.append(f"- バズ動画1位: {buzz_top['title']}({buzz_top['views']:,}回再生)")
    pv = today_views()
    if pv is not None:
        lines.append(f"- 本日の閲覧数(累計): {pv}回")
    for n in notes:
        lines.append(f"- ⚠ {n}")
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  [report] 日報記録: {path.name}")
