"""毎朝のフルパイプライン: カテゴリ別収集→選定→執筆→バズ動画集計→サイト生成→X告知"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timedelta, timezone

from src import announce, build, buzz, collect, editor, report, weekly

JST = timezone(timedelta(hours=9))

# フル便(全カテゴリ+バズ+X告知)の時間帯。それ以外の毎時便は1カテゴリ順繰りの軽量版
MAIN_HOURS = {7, 12, 17, 21}


def main() -> int:
    hour = datetime.now(JST).hour
    full = hour in MAIN_HOURS
    if full:
        targets = collect.CATEGORIES
        print(f"== フル便({hour}時) ==")
    else:
        keys = list(collect.CATEGORIES)
        k = keys[hour % len(keys)]
        targets = {k: collect.CATEGORIES[k]}
        print(f"== 軽量便({hour}時): {collect.CATEGORIES[k]} ==")

    published = build._load()
    recent_titles = [a["title"] for a in published[-40:]]
    articles, orig_titles, notes = [], [], []
    for cat, label in targets.items():
        print(f"[収集: {label}] (久遠)")
        candidates = collect.collect(cat)
        print(f"  候補: {len(candidates)}件")
        if not candidates:
            continue
        print(f"[選定・執筆: {label}] (真行寺)")
        try:
            picks = editor.select(candidates, cat, recent_titles)
        except Exception as e:
            print(f"  選定失敗(スキップ): {e}")
            notes.append(f"{label}の選定失敗: {e}")
            continue
        for p in picks:
            print(f"  OK [{p['source']}] {p['title']}")
            try:
                articles.append(editor.write_article(p))
                orig_titles.append(p["title"])
                recent_titles.append(p["title"])  # 同じ便の後続カテゴリでの重複選定を防ぐ
            except Exception as e:
                print(f"  執筆失敗({p['title']}): {e}")
                notes.append(f"執筆失敗: {p['title'][:40]}")

    print("[バズ動画TOP10] (久遠) — 毎時更新")
    videos = buzz.fetch_top10()
    if videos:
        # コメントは恒久キャッシュから引き継ぎ(ランク外→再ランクインでも再生成しない)、新規だけ生成
        prev_data = buzz.load()
        cache = dict(prev_data.get("comment_cache", {}))
        for v in prev_data.get("videos", []):
            if v.get("comment"):
                cache.setdefault(v["id"], v["comment"])
        for v in videos:
            v["comment"] = cache.get(v["id"], "")
        missing = [v for v in videos if not v["comment"]]
        if missing:
            try:
                for v, c in zip(missing, editor.buzz_comments(missing)):
                    v["comment"] = c
                print(f"  新規{len(missing)}本にコメント付与")
            except Exception as e:
                print(f"  コメント生成失敗(なしで続行): {e}")
        for v in videos:
            if v.get("comment"):
                cache[v["id"]] = v["comment"]
        cache = dict(list(cache.items())[-300:])  # 際限なく肥大させない
        buzz.save(videos, [v.get("comment", "") for v in videos], cache)

    print("[サイト生成] (八重樫)")
    if articles:
        build.save_articles(articles)
        collect.mark_posted([a["source_url"] for a in articles],
                            orig_titles + [a["title"] for a in articles])

    # 週刊まとめ: save_articles後に実行(未保存記事はdate/path未付与のため)。
    # 月曜7時を逃してもフル便で追いつき発行(week_ofが今週月曜より古ければ再生成)
    now = datetime.now(JST)
    if full:
        monday = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        wk = weekly.load()
        if not wk or wk.get("week_of", "") < monday:
            print("[週刊まとめ] (真行寺) — 週次発行")
            try:
                weekly.generate(build._load())
            except Exception as e:
                print(f"  週刊まとめ失敗(続行): {e}")

    build.build()

    if not articles and not videos:
        if full:
            print("フル便で記事もバズ動画もゼロ。異常終了")
            return 1
        print("軽量便: 新着なし(正常)")  # 既報除外後の候補ゼロは軽量便では普通(指摘8)
        return 0

    if full and articles:
        print("[X告知] (桐生)")
        try:
            announce.post(articles)
        except Exception as e:
            print(f"  X告知失敗(続行): {e}")
            notes.append(f"X告知失敗: {e}")
    elif full:
        print("[X告知] 記事ゼロのためスキップ(指摘15)")
    else:
        print("[X告知] 軽量便のためスキップ(コスト対策)")

    try:
        data = buzz.load()
        today = datetime.now(JST).strftime("%Y-%m-%d")
        buzz_top = (data.get("videos") or [None])[0] if data.get("date") == today else None
        report.write(articles, buzz_top, notes)
        mode_label = "フル便" if full else f"軽量便({next(iter(targets.values()))})"
        report.write_status(mode_label, articles, buzz_top, notes)
    except Exception as e:
        print(f"  日報記録失敗(続行): {e}")

    print("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
