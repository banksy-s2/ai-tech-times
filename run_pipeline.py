"""毎朝のフルパイプライン: カテゴリ別収集→選定→執筆→バズ動画集計→サイト生成→X告知"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src import announce, build, buzz, collect, editor, report


def main() -> int:
    published = build._load()
    recent_titles = [a["title"] for a in published[-40:]]
    articles, orig_titles, notes = [], [], []
    for cat, label in collect.CATEGORIES.items():
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

    print("[バズ動画TOP10] (久遠)")
    videos = buzz.fetch_top10()
    if videos:
        try:
            comments = editor.buzz_comments(videos)
        except Exception as e:
            print(f"  コメント生成失敗(コメントなしで続行): {e}")
            comments = []
        buzz.save(videos, comments)

    print("[サイト生成] (八重樫)")
    if articles:
        build.save_articles(articles)
        collect.mark_posted([a["source_url"] for a in articles],
                            orig_titles + [a["title"] for a in articles])
    build.build()

    if not articles and not videos:
        print("記事もバズ動画もゼロ。異常終了")
        return 1

    print("[X告知] (桐生)")
    try:
        announce.post(articles)
    except Exception as e:
        print(f"  X告知失敗(続行): {e}")
        notes.append(f"X告知失敗: {e}")

    try:
        buzz_top = (buzz.load().get("videos") or [None])[0]
        report.write(articles, buzz_top, notes)
    except Exception as e:
        print(f"  日報記録失敗(続行): {e}")

    print("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
