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
    ok_regions = 0
    for region in REGIONS:
        try:
            for v in _fetch_region(region, key):
                if v["id"] in merged:
                    merged[v["id"]]["regions"].append(region)
                else:
                    merged[v["id"]] = v
            ok_regions += 1
        except Exception as e:
            print(f"  [buzz] {region} 取得失敗: {e}")
    if ok_regions < 3:  # 半分以上失敗した部分集計で正常な前回データを上書きしない
        print(f"  [buzz] 取得成功{ok_regions}地域のみ → 前回データを維持")
        return None
    # 複数地域でバズっている動画を優先しつつ再生回数順
    top = sorted(merged.values(), key=lambda v: (len(v["regions"]), v["views"]), reverse=True)[:10]
    covered = sorted({r for v in merged.values() for r in v["regions"]}, key=REGIONS.index)
    for i, v in enumerate(top):
        v["rank"] = i + 1
    top[0]["_covered"] = covered  # 集計できた地域(部分取得時の表示に使う)
    print(f"  [buzz] {len(merged)}本から TOP10 を集計")
    return top


HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "buzz_history.json"


def save(videos: list[dict], comments: list[str], comment_cache: dict | None = None) -> None:
    for v, c in zip(videos, comments + [""] * 10):
        v["comment"] = c
    covered = videos[0].pop("_covered", None) if videos else None  # 集計できた地域(部分取得の明示)
    today = datetime.now(JST).strftime("%Y-%m-%d")
    storage.save_json(DATA_FILE, {
        "date": today,
        "videos": videos,
        "covered": covered or REGIONS,
        "comment_cache": comment_cache or {},
    })
    _append_history(today, videos)


def _append_history(day: str, videos: list[dict]) -> None:
    """日別TOP10を履歴に記録(その日の最終便の値で上書き)。殿堂入り集計と日別アーカイブの元データ"""
    hist = load_history()
    hist[day] = [{"rank": v["rank"], "id": v["id"], "title": v["title"], "channel": v["channel"],
                  "views": v["views"], "url": v["url"], "thumb": v["thumb"],
                  "regions": v.get("regions", []), "comment": v.get("comment", "")}
                 for v in videos]
    for old in sorted(hist)[:-400]:  # 400日分で頭打ち
        hist.pop(old, None)
    storage.save_json(HISTORY_FILE, hist)


def load_history() -> dict:
    return storage.load_json(HISTORY_FILE, {})


def hall_of_fame(hist: dict, limit: int = 20) -> list[dict]:
    """殿堂入り: ランクイン日数が多い順(同数なら最高順位→最大再生数)"""
    agg: dict = {}
    for day, rows in hist.items():
        if not isinstance(rows, list):
            continue
        seen_ids = set()
        for r in rows:
            if not isinstance(r, dict) or r.get("id") in seen_ids:
                continue  # 同一日の重複IDを日数として二重計上しない
            seen_ids.add(r.get("id"))
            a = agg.setdefault(r["id"], {"id": r["id"], "title": r["title"], "channel": r["channel"],
                                         "url": r["url"], "thumb": r["thumb"], "days": 0,
                                         "best": 99, "views": 0, "first": day, "last": day})
            a["days"] += 1
            a["best"] = min(a["best"], r["rank"])
            a["views"] = max(a["views"], r["views"])
            a["first"] = min(a["first"], day)
            a["last"] = max(a["last"], day)
            a["title"] = r["title"]
    return sorted(agg.values(), key=lambda x: (-x["days"], x["best"], -x["views"]))[:limit]


def load() -> dict:
    return storage.load_json(DATA_FILE, {"date": "", "videos": []})
