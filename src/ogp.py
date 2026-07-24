"""開発部長 八重樫慧: 記事ごとのOGP画像(SNSシェア時のアイキャッチ)を自動生成

1200x630のブランド画像を記事タイトル入りで作る。docs/ogp/<id>.png に保存。
既存ファイルはスキップ(毎便184枚を作り直さない)。Pillow + 游ゴシックを使用。
"""
from pathlib import Path

try:  # Pillow/日本語フォントが無い環境(Linux CI等)でもパイプライン全体を止めない
    from PIL import Image, ImageDraw, ImageFont
    _PIL_OK = True
except ImportError:  # pragma: no cover
    _PIL_OK = False

from .collect import CATEGORIES

DOCS = Path(__file__).resolve().parent.parent / "docs"
OGP_DIR = DOCS / "ogp"
FONT_BOLD = "C:/Windows/Fonts/YuGothB.ttc"
FONT_MED = "C:/Windows/Fonts/YuGothM.ttc"

W, H = 1200, 630
BG = (10, 14, 26)          # インクネイビー(サイトと同じ)
CARD = (27, 34, 54)
ACCENT = (255, 70, 53)     # シグナルの朱(上部帯)
AMBER = (246, 178, 60)     # 機械の琥珀
GOLD = (233, 180, 76)
TEXT = (236, 232, 223)     # 温かい新聞紙色
MUTED = (142, 148, 172)


def _is_valid_png(path: Path, w: int = 0, h: int = 0) -> bool:
    """PNGとして開けて期待サイズかを確認(サイズだけの判定では壊れ画像を見逃す)"""
    if not _PIL_OK:
        return path.exists()
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:  # verify後は再オープンが必要
            return (im.format == "PNG") and (not w or im.size == (w, h))
    except Exception:
        return False


def _save_atomic(img, out: Path) -> None:
    """一時ファイル経由で保存(中断しても壊れた画像を残さない)"""
    import os
    tmp = out.with_suffix(".tmp.png")
    img.save(tmp, "PNG")
    os.replace(tmp, out)


def _wrap(text: str, font, draw, max_w: int, max_lines: int) -> list[str]:
    """日本語向け: 1文字ずつ幅を測って折り返す"""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
            if len(lines) == max_lines - 1:
                break
    if cur:
        # 残りが入りきらなければ末尾を…に
        rest = text[sum(len(x) for x in lines):]
        while rest and draw.textlength(rest, font=font) > max_w:
            rest = rest[:-1]
        if rest != text[sum(len(x) for x in lines):]:
            rest = rest[:-1] + "…"
        lines.append(rest)
    return lines[:max_lines]


def generate(article: dict) -> str | None:
    """記事のOGP画像を生成しパス(/ogp/<id>.png)を返す。既存ならスキップ。失敗時None"""
    art_id = article["path"].rsplit("/", 1)[-1].replace(".html", "")
    out = OGP_DIR / f"{art_id}.png"
    rel = f"/ogp/{art_id}.png"
    if out.exists() and _is_valid_png(out, W, H):
        return rel  # 正常な画像は再生成しない
    if not _PIL_OK:
        return rel if out.exists() else None
    try:
        OGP_DIR.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 12], fill=ACCENT)                 # 上部アクセント帯
        f_logo = ImageFont.truetype(FONT_BOLD, 46)
        f_cat = ImageFont.truetype(FONT_BOLD, 34)
        f_title = ImageFont.truetype(FONT_BOLD, 68)
        f_url = ImageFont.truetype(FONT_MED, 32)

        d.text((70, 60), "AI TECH ", font=f_logo, fill=TEXT)
        lw = d.textlength("AI TECH ", font=f_logo)
        d.text((70 + lw, 60), "TIMES", font=f_logo, fill=AMBER)

        cat = CATEGORIES.get(article.get("category", "ai"), "AI")
        cw = d.textlength(cat, font=f_cat)
        d.rounded_rectangle([70, 150, 70 + cw + 40, 210], radius=8, fill=AMBER)
        d.text((90, 158), cat, font=f_cat, fill=BG)

        lines = _wrap(article["title"], f_title, d, W - 140, 4)
        y = 250
        for ln in lines:
            d.text((70, y), ln, font=f_title, fill=TEXT)
            y += 92

        d.line([70, H - 90, W - 70, H - 90], fill=(48, 54, 61), width=2)
        d.text((70, H - 66), "ai-tech-times.web.app", font=f_url, fill=AMBER)
        d.text((W - 360, H - 66), "AIが編集するニュース", font=f_url, fill=MUTED)

        _save_atomic(img, out)
        return rel
    except Exception as e:
        print(f"  [ogp] 生成失敗({art_id}): {e}")
        return None


def generate_logo() -> None:
    """schema.org publisher.logo 用の正方形ロゴ(docs/ogp/logo.png)。無ければ作る"""
    out = OGP_DIR / "logo.png"
    if (out.exists() and _is_valid_png(out, 512, 512)) or not _PIL_OK:
        return
    try:
        OGP_DIR.mkdir(parents=True, exist_ok=True)
        S = 512
        img = Image.new("RGB", (S, S), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S, 10], fill=ACCENT)
        f1 = ImageFont.truetype(FONT_BOLD, 92)
        f2 = ImageFont.truetype(FONT_BOLD, 92)
        d.text(((S - d.textlength("AI TECH", font=f1)) // 2, 180), "AI TECH", font=f1, fill=TEXT)
        d.text(((S - d.textlength("TIMES", font=f2)) // 2, 270), "TIMES", font=f2, fill=AMBER)
        _save_atomic(img, out)
    except Exception as e:
        print(f"  [ogp] ロゴ生成失敗: {e}")


def generate_default() -> None:
    """トップ/カテゴリ用のデフォルトOGP(docs/ogp/default.png)。無ければ作る"""
    out = OGP_DIR / "default.png"
    if (out.exists() and _is_valid_png(out, W, H)) or not _PIL_OK:
        return
    try:
        OGP_DIR.mkdir(parents=True, exist_ok=True)
        img = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 14], fill=ACCENT)
        f_logo = ImageFont.truetype(FONT_BOLD, 96)
        f_sub = ImageFont.truetype(FONT_MED, 40)
        f_url = ImageFont.truetype(FONT_MED, 34)
        t1 = "AI TECH "
        w1 = d.textlength(t1, font=f_logo)
        w2 = d.textlength("TIMES", font=f_logo)
        x0 = (W - (w1 + w2)) // 2
        d.text((x0, 210), t1, font=f_logo, fill=TEXT)
        d.text((x0 + w1, 210), "TIMES", font=f_logo, fill=AMBER)
        sub = "AIが24時間編集する総合ニュース"
        d.text(((W - d.textlength(sub, font=f_sub)) // 2, 350), sub, font=f_sub, fill=MUTED)
        url = "ai-tech-times.web.app"
        d.text(((W - d.textlength(url, font=f_url)) // 2, 470), url, font=f_url, fill=AMBER)
        _save_atomic(img, out)
    except Exception as e:
        print(f"  [ogp] デフォルト生成失敗: {e}")
