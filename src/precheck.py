"""再発防止の自動検査(鵜飼静): 過去に繰り返した同型ミスを毎便の頭で機械検知する

検知対象は全て「実際に一度以上やらかした」もの:
1. ps1への非ASCII混入(タスク0x1即死 ×2回)
2. 事務所ライブとカテゴリ定義の同期漏れ(×2回)
3. innerHTMLの新規使用(XSS入口 ×3回) — 基準値からの増加を検知
4. 公開中記事への助言表現・釣り文句の混入(×各1回)
検知したら警告文を返し、呼び出し元が日報・事務所ライブに載せる。
"""
import json
import re
from pathlib import Path

from .collect import CATEGORIES
from .editor import ADVICE_NG

ROOT = Path(__file__).resolve().parent.parent

HYPE_NG = ["衝撃", "ヤバい", "驚愕", "驚きの", "知られざる", "本当の理由", "本当の狙い", "全貌"]
INNERHTML_BASELINE = 3  # docs/office.html のシーン構築(信頼できる定数由来)のみ許容


def run() -> list[str]:
    warns = []

    for f in ["run_edition.ps1", "register_task.ps1", "finish_setup.ps1"]:
        p = ROOT / f
        if p.exists() and any(b > 127 for b in p.read_bytes()):
            warns.append(f"再発警報: {f}に非ASCII文字(タスク即死の恐れ)")

    try:
        office = (ROOT / "docs" / "office.html").read_text(encoding="utf-8")
        m = re.search(r"const CATS = \[(.*?)\];", office)
        if m:
            n = len([s for s in m.group(1).split(",") if s.strip()])
            if n != len(CATEGORIES):
                warns.append(f"再発警報: 事務所のカテゴリ表示({n})と実カテゴリ数({len(CATEGORIES)})が不一致")
    except OSError:
        pass

    cnt = 0
    for p in list((ROOT / "docs").glob("*.html")) + list((ROOT / "docs").glob("*.js")):
        try:
            cnt += p.read_text(encoding="utf-8").count(".innerHTML")
        except OSError:
            pass
    if cnt > INNERHTML_BASELINE:
        warns.append(f"再発警報: innerHTML使用が基準({INNERHTML_BASELINE})を超過({cnt}) — XSS再発リスク、要レビュー")

    try:
        arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
        for a in arts[-30:]:
            text = a["title"] + a["lead"] + " ".join(a["body"]) + " ".join(a.get("summary3") or [])
            if a.get("category") in ("stock", "jp_corp"):
                hit = next((x for x in ADVICE_NG if x in text), None)
                if hit:
                    warns.append(f"再発警報: 公開中記事に助言表現「{hit}」: {a['title'][:28]}")
            hype = next((x for x in HYPE_NG if x in a["title"]), None)
            if hype:
                warns.append(f"再発警報: 見出しに釣り文句「{hype}」: {a['title'][:28]}")
    except (OSError, json.JSONDecodeError, KeyError):
        pass

    return warns
