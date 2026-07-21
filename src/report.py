"""広報 桐生まひろ(兼務): 各便の日報を company/reports/ に自動記録"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .collect import CATEGORIES

REPORTS = Path(__file__).resolve().parent.parent / "company" / "reports"
JST = timezone(timedelta(hours=9))


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
    for n in notes:
        lines.append(f"- ⚠ {n}")
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  [report] 日報記録: {path.name}")
