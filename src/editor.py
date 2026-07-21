"""編集長 真行寺環: Gemini(無料枠)でネタ選定と記事執筆(REST直叩き・依存ゼロ)"""
import json
import os
import re
import time
import urllib.request

# 無料枠の日次クォータはモデル別。lite(枠大)を主力に、切れたら次へフォールバック
# ※gemini-flash-latestは2026-07時点でgemini-3.5-flashを指し、無料枠わずか20回/日
MODELS = ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-flash-latest"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# カテゴリごとの1回の更新あたりの掲載本数(1日4回更新×5本=20本/日)と選定基準
PICKS_PER_CATEGORY = {"ai": 2, "ai_jp": 2, "silicon": 2, "voices": 1, "influencer": 1, "world": 2}

SELECT_CRITERIA = {
    "ai": """- 海外の大手AI企業(OpenAI/Anthropic/Google/Meta/NVIDIA等)の新モデル・新製品・研究・業界に影響する出来事を優先
- 日本でまだ報じられていない海外の一次情報ほど価値が高い
- 単なるハウツー記事・宣伝・製品PRはノイズとして除外""",
    "ai_jp": """- 日本企業のAI活用、国産AIモデル、国内のAI規制・政策、日本のAIスタートアップの動きを優先
- 日本の読者の仕事や生活に直結する話題ほど価値が高い
- 展示会告知・製品PR・薄い活用事例はノイズとして除外""",
    "silicon": """- 米テック業界(シリコンバレー)の最新・速報性の高い動きを最優先(買収、資金調達、新製品、人事、規制、株価に響く発表など)
- 日本ではまだあまり報じられていない話題ほど価値が高い
- AIモデルの発表そのものはAIカテゴリと被るので、ビジネス・業界動向の切り口を優先""",
    "voices": """- 海外の著名なAI研究者・実務家「個人」の考察・意見・発見を紹介する枠
- 日本ではまだ知られていない視点や、業界の内側からの一次情報を優先
- 「誰が」言っているかが価値なので、発信者が明確なものだけ選ぶ""",
    "influencer": """- 国内外のインフルエンサー/YouTuber/TikToker/VTuberの話題性ある出来事を優先
- 記録達成、大型コラボ、プラットフォームの重要変更、社会的影響のある出来事など
- 根拠のないゴシップや個人攻撃的な話題は避ける""",
    "world": """- 世界と日本の重要ニュース(政治・経済・国際情勢・災害・社会)を優先
- 影響範囲が大きく、明日も語られるニュースを選ぶ
- 事件の凄惨な詳細が主題のものは避ける""",
}


def _gemini(prompt: str, json_mode: bool = True, models: list[str] | None = None) -> str:
    """モデルを順に試す。日次クォータ切れ(PerDay)は即次のモデルへ、瞬間的な429は待って再試行"""
    import urllib.error
    key = os.environ["GEMINI_API_KEY"]
    if models is None:
        models = MODELS
    gen_config = {"temperature": 0.4}
    if json_mode:
        gen_config["responseMimeType"] = "application/json"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }).encode("utf-8")
    last_error = None
    for model in dict.fromkeys(models):  # 重複モデルは1回だけ試す
        for attempt in range(2):  # タスクの30分制限内に収める(指摘4)
            req = urllib.request.Request(
                f"{API_BASE}/{model}:generateContent?key={key}", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=75) as r:
                    data = json.loads(r.read())
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", errors="replace")
                last_error = f"{model}: HTTP {e.code}"
                if e.code == 429 and "PerDay" in detail:
                    print(f"  [editor] {model} の日次枠切れ → 次のモデルへ")
                    break
                if attempt < 1:
                    print(f"  [editor] {model} 失敗(HTTP {e.code})、30秒後にリトライ")
                    time.sleep(30)
            except Exception as e:
                last_error = f"{model}: {e}"
                if attempt < 1:
                    time.sleep(15)
    raise RuntimeError(f"全モデル失敗: {last_error}")


def _parse_json(text: str):
    """最初に見つかった完全なJSON値を取り出す(前後の余計なテキストや2個目のJSONを無視)"""
    dec = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch in "[{":
            try:
                obj, _ = dec.raw_decode(text[i:])
                return obj
            except json.JSONDecodeError:
                continue
    return json.loads(text)


def select(candidates: list[dict], category: str, recent_titles: list[str] | None = None) -> list[dict]:
    """カテゴリごとの基準でトップN本を選定。既報の話題と候補内の重複を避ける"""
    n = PICKS_PER_CATEGORY[category]
    listing = "\n".join(
        f"{i}: [{c['source']}] {c['title']} — {c['summary'][:150]}"
        for i, c in enumerate(candidates))
    recent = ""
    if recent_titles:
        joined = "\n".join(f"- {t}" for t in recent_titles[-30:])
        recent = f"\n\n既に掲載済みの記事(同じ話題・同じ出来事は絶対に選ばない):\n{joined}"
    prompt = f"""あなたはニュースサイトの編集長です。以下の候補記事から、日本の読者が「思わずクリックして読みたくなる」ニュース価値の高い{n}本を選んでください。

読まれるニュースの条件(リサーチ済みの優先基準):
- お金に直結する話(株価・値上げ・買収額・収入への影響)
- 大物・有名企業/有名人の意外な動き
- 対立・訴訟・規制など「争い」の構図があるもの
- 読者の生活や仕事への影響が想像できるもの
- 規模を示す大きな数字があるもの

ルール:
- 同じ話題(同じ発表を扱った記事)は1本だけ選ぶ
{SELECT_CRITERIA[category]}{recent}

候補:
{listing}

JSON配列のみ出力: [{{"index": 数値, "reason": "選定理由1文"}}]"""
    # 選定は既報重複の見極めが命なので、指示追従が強い2.5-flashを優先
    data = _parse_json(_gemini(prompt, models=["gemini-2.5-flash"] + MODELS))
    if isinstance(data, dict):  # {"picks": [...]} 形式で返るケース
        data = next((v for v in data.values() if isinstance(v, list)), [data])
    picks = data[:n]
    return [candidates[p["index"]] for p in picks if 0 <= p.get("index", -1) < len(candidates)]


def write_article(item: dict) -> dict:
    """1本の候補を日本語記事に。元記事の要約にある事実のみ使用"""
    extra = ""
    if item.get("category") == "voices":
        extra = "\n- これは海外AI識者の発信の紹介記事。見出しと本文で「誰の発信か」を明示し、「〜氏は…と指摘しています」の形で本人の見解として書く"
    prompt = f"""あなたはニュースサイト「AI TECH TIMES」の記者です。以下の元記事情報だけを使って、日本語のニュース記事を書いてください。

元記事:
- 出典: {item['source']}
- タイトル: {item['title']}
- 要約: {item['summary']}
- URL: {item['url']}

厳守ルール:
- 上記の要約に書かれている事実だけを使う。数値・固有名詞・日付を推測で追加しない
- 元記事が英語の場合は自然な日本語に翻訳し、日本の読者に馴染みのない企業・人物には1文だけ補足を入れる{extra}
- 要約が薄い場合は、一般に知られている背景(企業の説明など)を1〜2文だけ補ってよいが、新事実は作らない
- 本文は500〜800字、です・ます調

見出し(タイトル)の勝ちパターン(必ず適用):
- 30字以内。具体的な数字(金額・%・倍率)を必ず入れる(元記事にある場合)
- 固有名詞(企業名・人名・製品名)を先頭近くに置く
- 「なぜ」「どうなる」と続きが気になる形、または読者の損得が分かる形にする
- ただし本文にない誇張・釣りは禁止。「衝撃」「ヤバい」等の乱用も禁止

JSONのみ出力:
{{"title": "日本語見出し", "lead": "1〜2文のリード文", "body": ["段落1", "段落2", "段落3"], "tags": ["タグ1", "タグ2", "タグ3"], "slug": "english-slug-with-hyphens"}}"""
    art = _parse_json(_gemini(prompt))
    if isinstance(art, list):  # [{...}] 形式で返るケース
        art = next((x for x in art if isinstance(x, dict)), {})
    # 保存前スキーマ検証: 欠損レコードを永続化するとサイト生成が連鎖失敗する(指摘2)
    if not isinstance(art, dict):
        raise ValueError("記事がdictでない")
    title = str(art.get("title", "")).strip()
    lead = str(art.get("lead", "")).strip()
    body = art.get("body")
    if isinstance(body, str):
        body = [body]
    if not isinstance(body, list):
        body = []
    body = [str(p).strip() for p in body if str(p).strip()]
    if not (title and lead and body):
        raise ValueError(f"記事スキーマ不正(title={bool(title)}, lead={bool(lead)}, body={len(body)}段落)")
    tags = art.get("tags")
    art.update({
        "title": title[:60], "lead": lead, "body": body,
        "tags": [str(t)[:20] for t in tags][:5] if isinstance(tags, list) else [],
    })
    art["slug"] = re.sub(r"[^a-z0-9-]", "", str(art.get("slug", "news")).lower())[:60] or "news"
    art["source"] = item["source"]
    art["source_url"] = item["url"]
    art["category"] = item.get("category", "ai")
    return art


def buzz_comments(videos: list[dict]) -> list[str]:
    """バズ動画ランキングへの一言コメント(10本まとめて1回で生成)"""
    listing = "\n".join(f"{i + 1}位: {v['title']} ({v['channel']}, {v['views']:,}回再生)"
                        for i, v in enumerate(videos))
    prompt = f"""以下は今日の世界のYouTube急上昇動画ランキングです。各動画に日本語の一言紹介コメント(30字以内、タイトルから分かる範囲のことだけ、断定しすぎない)を付けてください。

{listing}

出力形式(JSON不要、この{len(videos)}行だけ):
1: コメント
2: コメント
..."""
    text = _gemini(prompt, json_mode=False)  # タイトル内の引用符でJSONが壊れるため行形式
    comments = {}
    for line in text.splitlines():
        m = re.match(r"\s*(\d+)\s*[:：.]\s*(.+)", line)
        if m:
            comments[int(m.group(1))] = m.group(2).strip()
    return [comments.get(i + 1, "") for i in range(len(videos))]
