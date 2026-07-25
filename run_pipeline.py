"""毎朝のフルパイプライン: カテゴリ別収集→選定→執筆→バズ動画集計→サイト生成→X告知"""
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from datetime import datetime, timedelta, timezone

from src import announce, build, buzz, buzzcard, collect, editor, precheck, report, weekly

JST = timezone(timedelta(hours=9))

# フル便(全カテゴリ+バズ+X告知)の時間帯。それ以外の毎時便は1カテゴリ順繰りの軽量版
MAIN_HOURS = {7, 12, 17, 21}


def _abort(label: str, reason: str, notes: list) -> int:
    """便を中止する唯一の出口。ログと状態記録を必ず残してから終わる。

    注意: 終了コードが非ゼロだと run_edition.ps1 はデプロイをスキップするため、
    この状態は公開中のサイトには反映されない。異常の発見は logs/run.log と
    タスクの LastTaskResult に頼る(受容リスクR7)。
    """
    print(f"中止({label}): {reason}")
    try:
        report.write_status(f"中止({label})", [], None, notes + [f"{label}: {reason}"])
    except Exception as e:
        print(f"  状態記録失敗: {e}")
    return 1


def main() -> int:
    hour = datetime.now(JST).hour
    full = hour in MAIN_HOURS
    # 生成停止カテゴリ(著作権上の判断・collect.PAUSED_CATEGORIES)はフル便・軽量便とも対象から外す。
    # 綴り違いは二重防御(選定側と保存側)を同時に無効化するため、起動時に必ず突き合わせる
    unknown = collect.PAUSED_CATEGORIES - collect.CATEGORIES.keys()
    if unknown:
        return _abort("設定不正", f"停止カテゴリ名が存在しないキー: {sorted(unknown)}", [])
    active = {k: v for k, v in collect.CATEGORIES.items() if k not in collect.PAUSED_CATEGORIES}
    if not active:  # 全カテゴリ停止は設定ミスの可能性。空回しせず異常終了する
        return _abort("設定不正", "全カテゴリが生成停止中", [])
    if full:
        targets = active
        print(f"== フル便({hour}時) ==")
    else:
        # 軽量便どうしの通し番号で割り当てる(hourを直接割ると、フル便の時刻が抜けるぶん偏る)
        keys = list(active)
        slot = [h for h in range(24) if h not in MAIN_HOURS].index(hour)
        k = keys[slot % len(keys)]
        targets = {k: active[k]}
        print(f"== 軽量便({hour}時): {active[k]} ==")
    if collect.PAUSED_CATEGORIES:
        paused = ", ".join(collect.CATEGORIES.get(k, k) for k in sorted(collect.PAUSED_CATEGORIES))
        print(f"  生成停止中: {paused}")

    articles, notes = [], []
    orig_by_url: dict[str, str] = {}  # 保存できた記事だけを既報登録するための対応表

    # precheckは台帳を触る前に回す(壊れた台帳を素で読むと、警報を返す前に例外で落ちる)
    pre_warns = precheck.run()  # 同型ミスの再発を毎便検知(鵜飼)
    for w in pre_warns:
        print(f"  {w}")
    notes.extend(pre_warns)
    # 重大警報(安全弁の破れ・停止カテゴリの漏れ・検査不能)は、続行せず止める
    critical = [w for w in pre_warns if w.startswith("重大警報")]
    if critical:
        return _abort("重大警報", "原因を解消するまで便を回さないこと / " + " / ".join(critical), notes)

    try:
        published = build._check_ledger(build._load())
    except build.LedgerError as e:
        return _abort("台帳異常", f"{e} — サイトを作り直さずに終了する", notes)
    recent_titles = [a["title"] for a in published[-40:] if isinstance(a.get("title"), str)]
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
                art = editor.write_article(p)
                articles.append(art)
                if art.get("source_url"):
                    orig_by_url[art["source_url"]] = p["title"]
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
        if full:  # X投稿用サマリー画像はフル便のみ(当社固有データの露出・逆巻提案)
            card = buzzcard.generate(buzz.load())
            if card:
                print(f"  [buzzcard] {card}")
            else:  # 失敗を黙らせない(古い画像が「今日のTOP10」として残るため)
                print("  [buzzcard] 生成できず(Pillow不在/保存失敗)")
                notes.append("バズ画像の生成に失敗(today.pngが古い可能性)")

    print("[サイト生成] (八重樫)")
    if articles:
        # 既報登録は「保存できたものだけ」。先に登録すると、保存に失敗/破棄された記事が
        # 既報扱いになり二度と拾えなくなる(取りこぼしの恒久化)
        fed = len(articles)
        try:
            articles = build.save_articles(articles)
        except build.LedgerError as e:
            return _abort("台帳異常", f"{e} — 記事を保存せずに終了する", notes)
        if len(articles) < fed:
            notes.append(f"新着{fed}本のうち{fed - len(articles)}本が保存時に破棄された")
        if articles:
            urls = [a["source_url"] for a in articles if a.get("source_url")]
            try:
                collect.mark_posted(urls, [orig_by_url[u] for u in urls if u in orig_by_url]
                                    + [a["title"] for a in articles])
            except Exception as e:
                # 記事は保存済みなので便は続行する。既報登録の取りこぼしは、
                # 収集側の重複判定(URL一致/正規化タイトル/バイグラム類似)が受け止める
                print(f"  既報登録に失敗(続行): {e}")
                notes.append(f"既報登録に失敗: {e}")

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

    try:
        build.build()
    except build.LedgerError as e:
        return _abort("台帳異常", f"{e} — サイトを作り直さずに終了する", notes)

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
