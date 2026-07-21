"""リサーチャー 久遠汐里(兼務): 世界のYouTube急上昇からバズ動画TOP10を集計

YouTube Data API v3 の videos.list(chart=mostPopular) を主要6地域で叩き、
再生回数順に統合してTOP10を作る。1地域1ユニット/日なのでクォータはほぼ消費しない。
サムネイルはYouTube公式CDN(i.ytimg.com)のURLをそのまま使う。
"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import storage

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "buzz.json"
API_URL = "https://www.googleapis.com/youtube/v3/videos"
REGIONS = ["US", "GB", "JP", "KR", "BR", "IN"]
JST = timezone(timedelta(hours=9))


def _fetch_region(region: str, key: str) -> list[dict]:
    params = urllib.parse.urlencode({
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": 25,
        "key": key,
    })
    with urllib.request.urlopen(f"{API_URL}?{params}", timeout=20) as r:
        data = json.loads(r.read())
    videos = []
    for it in data.get("items", []):
        vid = it["id"]
        sn = it["snippet"]
        views = int(it.get("statistics", {}).get("viewCount", 0))
        videos.append({
            "id": vid,
            "title": sn["title"],
            "channel": sn["channelTitle"],
            "views": views,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "thumb": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            "regions": [region],
        })
    return videos


def fetch_top10() -> list[dict] | None:
    """全地域の急上昇を統合し再生回数順TOP10。APIキー未設定ならNone"""
    key = os.environ.get("YOUTUBE_API_KEY")
    if not key:
        print("  [buzz] YOUTUBE_API_KEY未設定のためスキップ")
        return None
    merged: dict[str, dict] = {}
    for region in REGIONS:
        try:
            for v in _fetch_region(region, key):
                if v["id"] in merged:
                    merged[v["id"]]["regions"].append(region)
                else:
                    merged[v["id"]] = v
        except Exception as e:
            print(f"  [buzz] {region} 取得失敗: {e}")
    if not merged:
        return None
    # 複数地域でバズっている動画を優先しつつ再生回数順
    top = sorted(merged.values(), key=lambda v: (len(v["regions"]), v["views"]), reverse=True)[:10]
    for i, v in enumerate(top):
        v["rank"] = i + 1
    print(f"  [buzz] {len(merged)}本から TOP10 を集計")
    return top


def save(videos: list[dict], comments: list[str]) -> None:
    for v, c in zip(videos, comments + [""] * 10):
        v["comment"] = c
    storage.save_json(DATA_FILE, {
        "date": datetime.now(JST).strftime("%Y-%m-%d"),
        "videos": videos,
    })


def load() -> dict:
    return storage.load_json(DATA_FILE, {"date": "", "videos": []})
