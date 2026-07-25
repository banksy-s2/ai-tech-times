"""広報 桐生まひろ: バズ動画TOP10の日次サマリー画像を生成(X投稿用)

当社固有データ(6地域のYouTube急上昇統合)を1枚の画像にする。
逆巻顧問の提案「待つより、誰も持っていないデータを出せ」の実装。
docs/buzz/card-YYYY-MM-DD.png に保存し、最新は docs/buzz/today.png としても置く。
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except ImportError:  # pragma: no cover
    _PIL_OK = False

DOCS = Path(__file__).resolve().parent.parent / "docs"
OUT_DIR = DOCS / "buzz"
FONT_BOLD = "C:/Windows/Fonts/YuGothB.ttc"
FONT_MED = "C:/Windows/Fonts/YuGothM.ttc"
JST = timezone(timedelta(hours=9))

W, H = 1200, 1560          # 縦長(Xのタイムラインで大きく表示される)
BG = (10, 14, 26)
CARD = (27, 34, 54)
SIGNAL = (255, 70, 53)
AMBER = (246, 178, 60)
TEXT = (236, 232, 223)
MUTED = (142, 148, 172)
LINE = (36, 44, 66)

REGION_JA = {"US": "米", "GB": "英", "JP": "日", "KR": "韓", "BR": "伯", "IN": "印"}
REGION_ORDER = ["US", "GB", "JP", "KR", "BR", "IN"]
KEEP_DAYS = 60  # 日付別カードの保持枚数(Git履歴と公開容量の肥大を防ぐ)


def _fit(text: str, font, draw, max_w: int) -> str:
    """幅に収まるよう末尾を…で詰める"""
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=font) > max_w:
        text = text[:-1]
    return text + "…"


def _views(n: int) -> str:
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}億回"
    if n >= 10_000:
        return f"{n / 10_000:.0f}万回"
    return f"{n:,}回"


def _prune_old_cards() -> None:
    """古い日付別カードを削除(最新KEEP_DAYS枚だけ残す)。today.pngは常に維持"""
    try:
        cards = sorted(OUT_DIR.glob("card-????-??-??.png"))
        for old in cards[:-KEEP_DAYS]:
            old.unlink()
    except OSError:
        pass


def generate(data: dict) -> str | None:
    """バズTOP10のサマリー画像を作りパスを返す。失敗時None"""
    if not _PIL_OK:
        return None
    videos = data.get("videos", [])
    if not videos:
        return None
    day = data.get("date") or datetime.now(JST).strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(day)):  # ファイル名に使う前に形式を検証
        day = datetime.now(JST).strftime("%Y-%m-%d")
    covered = [r for r in data.get("covered", REGION_ORDER) if r in REGION_JA] or REGION_ORDER
    region_txt = "・".join(REGION_JA[r] for r in covered)
    subtitle = (f"{day} 集計 ／ {region_txt}の急上昇を統合"
                if len(covered) == len(REGION_ORDER)
                else f"{day} 集計 ／ {region_txt}の急上昇を統合（一部地域は取得できず）")
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        f_logo = ImageFont.truetype(FONT_BOLD, 40)
        f_h1 = ImageFont.truetype(FONT_BOLD, 62)
        f_sub = ImageFont.truetype(FONT_MED, 30)
        f_rank = ImageFont.truetype(FONT_BOLD, 44)
        f_title = ImageFont.truetype(FONT_BOLD, 34)
        f_meta = ImageFont.truetype(FONT_MED, 26)
        f_foot = ImageFont.truetype(FONT_MED, 28)

        d.rectangle([0, 0, W, 14], fill=SIGNAL)
        d.text((60, 52), "AI TECH ", font=f_logo, fill=TEXT)
        d.text((60 + d.textlength("AI TECH ", font=f_logo), 52), "TIMES", font=f_logo, fill=AMBER)
        d.text((60, 120), "世界のバズ動画 TOP10", font=f_h1, fill=TEXT)
        d.text((60, 200), subtitle, font=f_sub, fill=MUTED)

        y = 265
        for v in videos[:10]:
            d.rounded_rectangle([50, y, W - 50, y + 105], radius=12, fill=CARD)
            rank = v.get("rank", 0)
            rc = AMBER if rank <= 3 else MUTED
            d.text((78, y + 30), f"{rank:>2}", font=f_rank, fill=rc)
            title = _fit(v.get("title", ""), f_title, d, W - 260)
            d.text((160, y + 22), title, font=f_title, fill=TEXT)
            regions = "・".join(REGION_JA.get(r, r) for r in v.get("regions", [])[:6])
            meta = f"{_fit(v.get('channel', ''), f_meta, d, 380)}　{_views(v.get('views', 0))}　{regions}"
            d.text((160, y + 66), meta, font=f_meta, fill=MUTED)
            y += 118

        d.line([60, H - 92, W - 60, H - 92], fill=LINE, width=2)
        d.text((60, H - 68), "毎時更新 ／ ai-tech-times.web.app/buzz.html", font=f_foot, fill=AMBER)

        out = OUT_DIR / f"card-{day}.png"
        tmp = out.with_suffix(".tmp.png")
        img.save(tmp, "PNG")
        import os
        os.replace(tmp, out)
        # 最新版の固定URL(Xで毎日同じURLを使えるように)
        today = OUT_DIR / "today.png"
        tmp2 = today.with_suffix(".tmp.png")
        img.save(tmp2, "PNG")
        os.replace(tmp2, today)
        _prune_old_cards()
        return f"/buzz/card-{day}.png"
    except Exception as e:
        print(f"  [buzzcard] 生成失敗: {e}")
        return None
