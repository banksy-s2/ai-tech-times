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
from datetime import datetime
from pathlib import Path

from .collect import CATEGORIES, PAUSED_CATEGORIES, PAUSED_SINCE
from .editor import ADVICE_NG

ROOT = Path(__file__).resolve().parent.parent

HYPE_NG = ["衝撃", "ヤバい", "驚愕", "驚きの", "知られざる", "本当の理由", "本当の狙い", "全貌"]
# docs/office.htmlのシーン構築(社員デスク/凪/顧問/カウントダウン)のみ許容。
# いずれも埋め込む値はコード内の定数で、外部データは一切通らない(通す場合はtextContentを使うこと)。
# この数値を上げるときは、新規箇所が本当に定数由来かを必ず確認する。
INNERHTML_BASELINE = 4


def _safety_valves() -> list[str]:
    """安全弁が生きているかを毎便テストする(第6回事故: 削除機能の暴走)。
    実際に危険な入力を流し、"何もしない"ことを確認する。非破壊。"""
    out = []
    try:
        from . import build
        before = {d: sorted(p.name for p in (ROOT / "docs" / d).iterdir())
                  for d in ("articles", "term", "ogp", "archive")
                  if (ROOT / "docs" / d).is_dir()}
        if not before:
            return out
        for label, arts, td in (("空データ", [], {}), ("1件だけ", build._load()[:1], {"x": {"slug": "x", "latest": "2026-01-01"}})):
            build._sweep_orphans(arts, td)
        after = {d: sorted(p.name for p in (ROOT / "docs" / d).iterdir())
                 for d in before}
        for d in before:
            lost = set(before[d]) - set(after.get(d, []))
            if lost:
                out.append(f"重大警報: 安全弁が破られた({d}で{len(lost)}件削除) — 削除機能を至急停止すること")
    except Exception as e:
        # 削除機能の安全弁が生きているか確認できないまま _sweep_orphans まで進ませない。
        # 「検査不能」は「異常なし」ではない(フェイルクローズ)
        out.append(f"重大警報: 安全弁テストが実行できない({e}) — 削除機能の健全性を確認できない")
    return out


def _paused_leak() -> list[str]:
    """生成停止カテゴリ(著作権上の判断・D1)の記事が新たに公開されていないか。
    本番台帳への書き込みテストは禁止のため、"漏れた結果"を検出する方式にする。非破壊。"""
    if not PAUSED_CATEGORIES:
        return []
    path = ROOT / "data" / "articles.json"
    if not path.exists():
        return []  # 開設初日など。記事が存在しない以上、漏れようがない
    try:
        arts = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        # 読めない=漏れていないことを確認できない。検査不能は重大扱いにして便を止める
        return [f"重大警報: 停止カテゴリ検査が実行できない({e})"]
    if not isinstance(arts, list):
        return ["重大警報: 停止カテゴリ検査が実行できない(台帳の形式が不正)"]
    try:
        since = datetime.strptime(PAUSED_SINCE, "%Y-%m-%d %H:%M")
    except ValueError:
        return [f"重大警報: 停止発効日時の書式が不正({PAUSED_SINCE})"]
    leaked, unparsable = [], 0
    for a in arts:
        if not isinstance(a, dict):
            unparsable += 1  # 台帳に非dictが混ざるのは異常。見逃さない
            continue
        if a.get("category") not in PAUSED_CATEGORIES:
            continue
        # 停止発効より後に公開されたものだけが「漏れ」。同日午前の既存記事と区別するため時刻まで見る
        try:
            when = datetime.strptime(f"{a['date']} {a['time']}", "%Y-%m-%d %H:%M")
        except (KeyError, TypeError, ValueError):
            unparsable += 1
            continue
        if when >= since:
            leaked.append(a)
    out = []
    if leaked:
        out.append(f"重大警報: 生成停止カテゴリの記事が{len(leaked)}本公開されている"
                   f"({leaked[0].get('category')}) — 生成経路を至急確認すること")
    if unparsable:
        out.append(f"重大警報: 停止カテゴリ検査で日時を判定できない記事が{unparsable}件 — 検査不能")
    return out


def run() -> list[str]:
    warns = list(_safety_valves())
    warns += _paused_leak()

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

    # 台帳が壊れていても、ここで例外を出して警報そのものを握り潰さないこと
    # (壊れた台帳は上の _paused_leak が重大警報として既に報告している)
    try:
        arts = json.loads((ROOT / "data" / "articles.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        arts = []
    for a in (arts[-30:] if isinstance(arts, list) else []):
        if not isinstance(a, dict) or not isinstance(a.get("title"), str):
            continue
        try:
            text = a["title"] + a["lead"] + " ".join(a["body"]) + " ".join(a.get("summary3") or [])
        except (KeyError, TypeError):
            continue
        if a.get("category") in ("stock", "jp_corp"):
            hit = next((x for x in ADVICE_NG if x in text), None)
            if hit:
                warns.append(f"再発警報: 公開中記事に助言表現「{hit}」: {a['title'][:28]}")
        hype = next((x for x in HYPE_NG if x in a["title"]), None)
        if hype:
            warns.append(f"再発警報: 見出しに釣り文句「{hype}」: {a['title'][:28]}")

    return warns
