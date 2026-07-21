"""広報 桐生まひろ: 新着記事をXに告知(トークン未設定時はスキップ)"""
import os
from datetime import datetime, timedelta, timezone

BASE_URL = "https://banksy-s2.github.io/ai-tech-times"
JST = timezone(timedelta(hours=9))

X_ENV_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")

# 更新スロット別のおっちゃん挨拶(朝7:00/昼12:30/夕方17:30/夜21:30)
GREETINGS = [
    (10, "おはようさん。おっちゃんが今朝のニュース拾ってきたで。"),
    (15, "昼メシのお供にどうぞや。昼のニュースやで。"),
    (20, "おつかれさん。夕方のニュース置いとくで。"),
    (24, "今日も一日おつかれさん。寝る前に夜のニュースや。"),
]


def compose(articles: list[dict]) -> str:
    """おっちゃん文体(@ganmenmahi1020)。URLを入れると$0.20/回(テキストのみは$0.015)なのでURL禁止"""
    hour = datetime.now(JST).hour
    greeting = next(g for limit, g in GREETINGS if hour < limit)
    lines = [greeting]
    for a in articles[:3]:
        t = a["title"]
        lines.append(f"▶ {t[:24]}{'…' if len(t) > 24 else ''}")
    lines.append("続きはプロフのリンクからな。")
    return "\n".join(lines)


def post(articles: list[dict]) -> None:
    if not all(os.environ.get(k) for k in X_ENV_KEYS):
        print("  [announce] Xトークン未設定のためスキップ")
        return
    import tweepy
    client = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )
    resp = client.create_tweet(text=compose(articles))
    print(f"  [announce] X投稿完了 id={resp.data['id']}")
