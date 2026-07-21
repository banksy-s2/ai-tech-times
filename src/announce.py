"""広報 桐生まひろ: 新着記事をXに告知(トークン未設定時はスキップ)"""
import os

BASE_URL = "https://banksy-s2.github.io/ai-tech-times"

X_ENV_KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")


def compose(articles: list[dict]) -> str:
    lines = ["【今朝のAIニュース】"]
    for a in articles[:3]:
        lines.append(f"▶ {a['title']}")
    lines.append(f"{BASE_URL}/")
    lines.append("#AIニュース #生成AI")
    return "\n".join(lines)[:270]


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
