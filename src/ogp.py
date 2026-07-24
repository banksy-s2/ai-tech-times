"""開発部長 八重樫慧: 記事ごとのOGP画像(SNSシェア時のアイキャッチ)を自動生成

1200x630のブランド画像を記事タイトル入りで作る。docs/ogp/<id>.png に保存。
既存ファイルはスキップ(毎便184枚を作り直さない)。Pillow + 游ゴシックを使用。
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .collect import CATEGORIES

DOCS = Path(__file__).resolve().parent.parent / "docs"
OGP_DIR = DOCS / "ogp"
FONT_BOLD = "C:/Windows/Fonts/YuGothB.ttc"
FONT_MED = "C:/Windows/Fonts/YuGothM.ttc"

W, H = 1200, 630
BG = (13, 17, 23)          # サイトと同じダーク
CARD = (22, 27, 34)
ACCENT = (247, 129, 102)   # accent2
GOLD = (227, 179, 65)
TEXT = (230, 237, 243)
MUTED = (139, 148, 158)


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
    if out.exists():
        return rel
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
        d.text((70 + lw, 60), "TIMES", font=f_logo, fill=ACCENT)

        cat = CATEGORIES.get(article.get("category", "ai"), "AI")
        cw = d.textlength(cat, font=f_cat)
        d.rounded_rectangle([70, 150, 70 + cw + 40, 210], radius=10, fill=ACCENT)
        d.text((90, 158), cat, font=f_cat, fill=BG)

        lines = _wrap(article["title"], f_title, d, W - 140, 4)
        y = 250
        for ln in lines:
            d.text((70, y), ln, font=f_title, fill=TEXT)
            y += 92

        d.line([70, H - 90, W - 70, H - 90], fill=(48, 54, 61), width=2)
        d.text((70, H - 66), "ai-tech-times.web.app", font=f_url, fill=GOLD)
        d.text((W - 360, H - 66), "AIが編集するニュース", font=f_url, fill=MUTED)

        img.save(out, "PNG")
        return rel
    except Exception as e:
        print(f"  [ogp] 生成失敗({art_id}): {e}")
        return None


def generate_default() -> None:
    """トップ/カテゴリ用のデフォルトOGP(docs/ogp/default.png)。無ければ作る"""
    out = OGP_DIR / "default.png"
    if out.exists():
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
        d.text((x0 + w1, 210), "TIMES", font=f_logo, fill=ACCENT)
        sub = "AIが24時間編集する総合ニュース"
        d.text(((W - d.textlength(sub, font=f_sub)) // 2, 350), sub, font=f_sub, fill=MUTED)
        url = "ai-tech-times.web.app"
        d.text(((W - d.textlength(url, font=f_url)) // 2, 470), url, font=f_url, fill=GOLD)
        img.save(out, "PNG")
    except Exception as e:
        print(f"  [ogp] デフォルト生成失敗: {e}")
