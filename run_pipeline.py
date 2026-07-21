"""毎朝のフルパイプライン: 収集→選定→執筆→サイト生成→X告知"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src import announce, build, collect, editor


def main() -> int:
    print("[1/5] RSS収集(久遠)")
    candidates = collect.collect()
    print(f"  候補: {len(candidates)}件")
    if not candidates:
        print("候補ゼロ。サイトだけ再生成して終了")
        build.build()
        return 0

    print("[2/5] トップ3選定(真行寺)")
    picks = editor.select(candidates)
    for p in picks:
        print(f"  OK [{p['source']}] {p['title']}")

    print("[3/5] 記事執筆(真行寺)")
    articles = []
    for p in picks:
        try:
            articles.append(editor.write_article(p))
        except Exception as e:
            print(f"  執筆失敗({p['title']}): {e}")
    if not articles:
        print("執筆ゼロ。異常終了")
        return 1

    print("[4/5] サイト生成(八重樫)")
    build.save_articles(articles)
    build.build()
    collect.mark_posted([a["source_url"] for a in articles])

    print("[5/5] X告知(桐生)")
    try:
        announce.post(articles)
    except Exception as e:
        print(f"  X告知失敗(続行): {e}")

    print("完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
