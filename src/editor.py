"""編集長 真行寺環: Gemini(無料枠)でネタ選定と記事執筆(REST直叩き・依存ゼロ)"""
import json
import os
import re
import time
import urllib.request

# 無料枠の日次クォータはモデル別。lite(枠大)を主力に、切れたら次へフォールバック
# ※gemini-flash-latestは2026-07時点でgemini-3.5-flashを指し、無料枠わずか20回/日
MODELS = ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-flash-latest"]

# 投資助言の禁止表現(株式・日本企業カテゴリの公開前検査+precheckの再発監視で共用)
ADVICE_NG = ["買い時", "売り時", "買うべき", "売るべき", "買い推奨", "売り推奨", "推奨銘柄",
             "おすすめ銘柄", "目標株価", "必ず上がる", "上昇が期待でき", "今のうちに買", "仕込み時", "狙い目"]
API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# カテゴリごとの1回の更新あたりの掲載本数(1日4回更新×5本=20本/日)と選定基準
PICKS_PER_CATEGORY = {"ai": 2, "ai_jp": 2, "silicon": 2, "voices": 1, "influencer": 1, "world": 2, "stock": 2, "jp_corp": 2}

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
    "stock": """- 日本の株式市場・投資家に影響する最新ニュースを最優先(日経平均・東証の動き、日銀・金利、為替、大型決算、NISA等の制度変更)
- 「市場がなぜ動いたか」の材料が明確なもの、投資家の判断材料になる事実があるものほど価値が高い
- 特定銘柄の推奨・煽り・投資助言まがいの記事はノイズとして除外""",
    "jp_corp": """- **日本の企業のみ**。海外企業(Google/Apple/Meta等)が主語の話は選ばない(シリコンバレー欄の担当)
- 日本の上場企業の経営に関わる出来事を優先(決算・業績修正、提携・買収、新事業・撤退、不祥事・リコール、大型人事)
- 誰もが知る大企業の動き、または無名でも影響の大きい出来事ほど価値が高い
- 市場全体の話(日経平均・為替)は株式投資カテゴリの担当なので、ここでは「個別企業」の話だけを選ぶ
- 特定銘柄の推奨・投資助言まがいはノイズとして除外""",
}


def _budget_ok() -> bool:
    """Gemini日次呼び出し予算(論理タスク数)。無料枠の枯渇連鎖と30分制限の衝突を防ぐ"""
    from datetime import datetime, timedelta, timezone
    from pathlib import Path
    from . import storage
    path = Path(__file__).resolve().parent.parent / "data" / "gemini_budget.json"
    today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
    data = storage.load_json(path, {})
    if data.get("date") != today:
        data = {"date": today, "count": 0}
    data["count"] += 1
    storage.save_json(path, data)
    if data["count"] > 200:
        print(f"  [editor] 日次予算200回を超過({data['count']}) → 呼び出し停止")
        return False
    return True


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
            if not _budget_ok():  # 予算は実HTTPリクエスト単位で数える(障害時のリトライも計上)
                raise RuntimeError("Gemini日次予算超過")
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
    picks, used = [], set()
    for p in data:
        if len(picks) >= n:
            break
        i = p.get("index", -1) if isinstance(p, dict) else -1
        if 0 <= i < len(candidates) and i not in used:  # 同一便内の重複index排除
            used.add(i)
            picks.append(candidates[i])
    return picks


def write_article(item: dict) -> dict:
    """1本の候補を日本語記事に。元記事の要約にある事実のみ使用"""
    extra = ""
    if item.get("category") == "voices":
        extra = "\n- これは海外AI識者の発信の紹介記事。見出しと本文で「誰の発信か」を明示し、「〜氏は…と指摘しています」の形で本人の見解として書く"
    elif item.get("category") in ("stock", "jp_corp"):
        extra = "\n- これは株式・企業ニュース。数値・発表内容など事実のみを伝え、売買の推奨・将来の株価予想・「今が買い時」等の投資助言にあたる表現は絶対に書かない"
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

見出し(タイトル)の心理学ルール(研究知見ベース・必ず適用):
- 【情報の半開き】核心の事実(誰が・何を・数字)は具体的に見せ、「なぜ」「この後どうなる」のうち**1つだけ**を隠して読む理由を作る。全部隠す曖昧見出しは研究上クリックが下がるので禁止
- 【自分ごと化】読者の仕事・生活・財布にどう関わるかが想像できる言葉を選ぶ
- 【損失回避】「知らないと損・困る」性質のニュースは、それが伝わる形にする
- 【意外性】常識と逆の出来事は対比を見出しに出す(「”○○なのに”△△」の構図)
- 【具体数字】金額・%・倍率は必ず入れる(元記事にある場合のみ)
- 【固有名詞先頭】有名企業・大物の名前は先頭近くに(視認性と権威)
- 30字以内。禁止ワード:「衝撃」「ヤバい」「驚愕」「驚きの」「知られざる」「本当の理由/狙い」「罠」「全貌」「裏側」— 中身が約束できない釣り文句は信頼を削るため使わない。本文にない誇張・数字の捏造も禁止。信頼が最大の資産
- 【出力前の自己検証】見出しに入れた数字・固有名詞が自分の書いたリード/本文に存在するか確認し、無ければ見出しから外して書き直す

people(人物注釈)のルール:
- 記事本文に登場する「実在の著名人」(経営者・政治家・研究者・タレント等)だけを最大3人
- nameは**本文で使った表記そのまま**(例: 本文が「アルトマン氏」なら name も「アルトマン氏」)
- bioは30〜60字で、広く知られた確実な事実のみ(肩書・所属・代表的な実績)。少しでも不確かな人物は含めない
- 該当者がいなければ空配列

summary3(3行まとめ): 記事の要点を3行(各25字以内)で。忙しい読者が本文を読まなくても核心が分かるように

terms(企業・AI注釈)のルール:
- 本文に登場する「実在の企業」と「AIモデル/AI製品」を合計最大4つ
- typeは "company"(企業) か "ai"(AIモデル・AI製品)
- nameは本文で使った表記そのまま
- descは30〜60字。企業なら「何の会社か(本拠・主要事業)」、AIなら「開発元と何をするAIか・特徴」
- 広く知られた確実な事実のみ。少しでも不確かなら含めない。記事の主題そのものより「読者が知らなそうなもの」を優先

JSONのみ出力:
{{"title": "日本語見出し", "lead": "1〜2文のリード文", "summary3": ["要点1", "要点2", "要点3"], "body": ["段落1", "段落2", "段落3"], "tags": ["タグ1", "タグ2", "タグ3"], "slug": "english-slug-with-hyphens", "people": [{{"name": "本文中の表記", "bio": "人物紹介30〜60字"}}], "terms": [{{"name": "本文中の表記", "type": "company", "desc": "説明30〜60字"}}]}}"""
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
    # 投資助言ガード(株式カテゴリ): プロンプト頼みにせず公開前に機械検査、検出したら記事ごと破棄
    if item.get("category") in ("stock", "jp_corp"):
        s3_raw = art.get("summary3")
        s3_text = " ".join(str(s) for s in s3_raw) if isinstance(s3_raw, list) else ""
        full_text = title + lead + " ".join(body) + s3_text  # 3行まとめも検査対象(指摘3)
        hit = next((w for w in ADVICE_NG if w in full_text), None)
        if hit:
            raise ValueError(f"投資助言表現を検出({hit})のため記事破棄")
    tags = art.get("tags")
    people = art.get("people")
    clean_people = []
    if isinstance(people, list):
        for p in people[:3]:  # プロンプト仕様(最大3人)と一致させる
            if isinstance(p, dict) and str(p.get("name", "")).strip() and str(p.get("bio", "")).strip():
                name = str(p["name"]).strip()[:30]
                if name not in " ".join(body) + lead:  # 本文に登場しない人物は注釈しない
                    continue
                clean_people.append({"name": name, "bio": str(p["bio"]).strip()[:80]})
    terms = art.get("terms")
    clean_terms = []
    if isinstance(terms, list):
        body_text = " ".join(body) + lead
        for t in terms[:4]:
            if (isinstance(t, dict) and str(t.get("name", "")).strip() and str(t.get("desc", "")).strip()
                    and t.get("type") in ("company", "ai")):
                name = str(t["name"]).strip()[:30]
                if len(name) >= 3 and name in body_text:  # 表示側の下限(3文字)と一致させる
                    clean_terms.append({"name": name, "type": t["type"], "desc": str(t["desc"]).strip()[:80]})
    s3 = art.get("summary3")
    art.update({
        "terms": clean_terms,
        "title": title[:60], "lead": lead, "body": body,
        "tags": [str(t)[:20] for t in tags][:5] if isinstance(tags, list) else [],
        "people": clean_people,
        "summary3": [str(s).strip()[:30] for s in s3 if str(s).strip()][:3] if isinstance(s3, list) else [],
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
