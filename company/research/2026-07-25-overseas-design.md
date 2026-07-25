# 海外ニュースサイトの設計・記事の出し方 調査 — 2026-07-25

依頼: 社長「海外のニュースサイトもどんな設計、記事の出し方」
**すべて実際にfetchした実データ。推測は含まない。**

## 0. 取得可否(正直に記録)

| サイト | 結果 |
|---|---|
| AP News / BBC / Guardian / Al Jazeera / Semafor / CNBC | ○ トップ+記事本文 |
| Axios | homepageは**403**。公式RSSが全文配信のため**記事100本の本文を取得**(Smart Brevity解析はここから) |
| Politico / Quartz / Business Insider | homepage 403、**RSSのみ** |
| **Reuters** | **401。取得不可** |
| Bloomberg | 未取得 |
| 追加取得 | **text.npr.org** / **lite.cnn.com**(画像ゼロのテキスト専用版)← 当社に最も近い |

## 1. 記事本文の構造

### Axios(Smart Brevity) — 記事100本から定型ラベルを機械集計

構造: **導入1段落(ラベルなし・約35語で結論)** → 以降すべて**太字ラベル＋コロン**の短ブロック＋箇条書き

出現回数(100本中):
```
87 Why it matters:      20 The intrigue:        11 What's next:
48 Driving the news:    20 The other side:      10 Reality check:
45 The big picture:     17 Yes, but:             7 Behind the scenes:
37 Zoom in:             17 State of play:        7 Context:
35 Between the lines:   16 What to watch:        6 Friction point:
30 Zoom out:            15 Catch up quick:       6 Threat level:
30 The bottom line:     13 Go deeper:            4 Flashback:
29 What they're saying: 12 By the numbers:       4 What we're hearing:
```
- 2ブロック目が `Why it matters:` = **87%**
- 社の見解は絵文字ラベルで明示: `💭 Thought bubble, from Axios media correspondent Sara Fischer:`
- 更新履歴を本文末に平文で: `This story has been updated with comments in reaction to the panel's vote.`

### Semafor(Semaform) — 261本から集計

`The News 35` / `Know More 40` / `Room for Disagreement 21` / `Notable 48` / `The Scoop 11` /
**`○○'s view`(記者ファーストネーム+'s view)が20本以上**

実物の並び:
```
The News → Know More → The View From Zambia → Ruben's view → Room for Disagreement
```
**事実 / 記者の見解 / 反対意見 を構造的に分離**しているのが核心。

### その他

- **CNBC**: 冒頭に `Key Points`(箇条書き3点、各1文)。段落平均25語
- **AP**: `CAIRO (AP) —` のダテライン付きリード1段落(39語)。解説記事は文章型小見出し
- **BBC**: リード26語で全結論。**小見出しゼロ・39段落・平均26.6語**。末尾に固定の背景説明ブロック
- **NPR**: `Here are five takeaways...` → `1. No immediate relief...` の番号付き小見出し

## 2. 記事の長さ(実測・英語words)

| 種別 | 実測 |
|---|---|
| Axios(100本分布) | 最短175 / **中央値486** / 最長976 |
| Semafor 短形式 | 約160語(3箇条書きのみで完結) |
| Semafor Semaform | 860〜1,628 |
| AP ストレート速報 | 466語 / 13段落(`2 MIN READ`) |
| AP 解説 | 1,123語 / 31段落(`5 MIN READ`) |
| BBC | 1,038語 / 39段落 |
| Guardian | 958語 / 26段落 |
| CNBC | 963語 / 38段落 |

**リード段落は全社26〜39語(日本語150〜240字相当)に収束。段落平均25〜37語。**

## 3. トップページの情報設計

- **AP**: 全リンクに「**N MIN READ**」と**コメント数**が付く。出来事ハブ+切り口4本を最上段に
- **BBC**: **階層が3段** — ①要約あり6本 ②見出しのみ5本 ③番号付きリスト(Most read 1〜10)
- **Al Jazeera**: `list 1 of 10` の縦積みライブ更新枠(各行に相対時刻+見出しのみ)
- **Guardian**: 全記事に**キッカー(トピック名)を見出しの上**に(`Live` / `Explainer` / `Analysis` / `Video`)。各ブロックに `Hide` ボタン
- **Semafor**: セクション別の縦積み。各項目は**見出し+1文要約のみ、タイムスタンプなし**

## 4. 時刻・鮮度の見せ方(実物表記)

| サイト | 表記 |
|---|---|
| BBC | 相対のみ `9 mins ago` `4 hrs ago` `1 day ago` |
| Al Jazeera | **二重表記** `Published 4 minutes ago` + `4m ago`。古い記事は絶対 |
| Guardian | 一覧は相対、記事は**絶対+初出時刻** `First published on Sat 25 Jul 2026 00.28 BST` |
| CNBC | **公開と更新を併記** `Published Fri, Jul 24 ... / Updated Fri, Jul 24 ...` |
| AP | 相対 + **`N MIN READ`が鮮度と別の指標**として全項目に |

LIVE表示: BBC=`LIVE`バッジ / AJ=`BREAKING`+点滅ドット / Guardian=見出し末尾に ` – live` / CNBC=`: Live updates`
CNBCのライブブログは JSON-LD `LiveBlogPosting` を出力し、**37件の更新それぞれに個別の見出しと時刻**。

## 5. 記事の分類

- **AP**: JSON-LDの `keywords` が**16個**。粒度混在が特徴 —
  大分類(`World news`)/出来事名(`Iran war`)/地名(`Tehran`)/人名(`Ali Khamenei`)/組織(`Iran government`)
- **AP のサブセクション**が事実上のトピックページ: `Iran war` `Tariffs` `America at 250` `India Focus`
  → **継続中の出来事名がそのまま常設カテゴリになっている**
- **BBC**: タグは2個だけ(出来事タグ+地域タグの2本立て)
- **Guardian**: **記事種別 `news` までタグ化**

## 6. 1つの出来事を複数記事に分ける方法 ← 当社に最も応用が効く

**APトップ最上段の実物**:
```
Iran war                                          ← 出来事ハブ名
 ├ War powers vote        ├ Why Hormuz matters
 ├ Oil producers bypass strait  ├ Consumers feel the pinch   ← 切り口4本を先に提示
Bridges and infrastructure hit as US struck deeper inside Iran  ← 主記事(5 MIN READ)
More Coverage
 ├ Iran reports no new U.S. strikes (2 MIN READ)  ← 速報
 └ UNESCO adds West Bank site... (3 MIN READ)      ← 波及
```

**実測された切り口6種**:
1. 速報(466語/2 MIN)
2. 現状まとめ(1,123語/5 MIN、小見出しで時系列分割)
3. 背景解説(`Why ○○ matters`)
4. 生活への影響(`Consumers feel the pinch`)
5. 写真1枚もの(1 MIN)
6. 反応・続報(`Protesters vow to press on`)

回遊: CNBCは**本文の途中**に関連11本を差し込む / Axiosは `Go deeper:` / BBCは記事末 `Related`+`More from the BBC`

## 7. 見出しの型(実測統計)

| 媒体 | n | 文字数中央値 | 語数中央値 | コロン率 | 数字入り | 引用符 | 疑問形 |
|---|---|---|---|---|---|---|---|
| Semafor | 261 | **50** | **8** | 2% | 9% | 11% | 0.4% |
| Axios | 100 | **56** | **9** | 23% | 18% | 38% | 1% |
| Politico | 30 | 55 | 9 | 13% | 17% | 43% | 10% |
| Quartz | 22 | 66 | 11 | 0% | **73%** | 9% | 0% |
| Al Jazeera | 25 | 71 | 11 | 24% | 20% | 36% | 8% |
| BBC | 25 | 71 | 11 | 24% | 8% | 28% | 16% |
| Guardian | 111 | **82** | 14 | **48%** | 14% | **56%** | 18% |
| CNBC | 30 | 83 | 14 | 10% | 30% | 17% | 0% |
| Business Insider | 20 | **91** | **16** | 5% | 40% | 55% | 5% |

**要約文(dek)の長さ中央値**: BBC 108字 / AJ 115字 / Politico 123字 / Semafor 132字 / CNBC 137字
→ **110〜140字が標準**

### 構文パターン
- **全社ほぼ100%が能動態・現在形**(`resigns` `wins` `pauses`)。受動態は行為者不明時のみ(`Ten killed in...`)
- **冠詞・be動詞の省略**が徹底
- コロンの用途は2種: **(a)ラベル**(`Scoop:` `EXPLAINER`) **(b)要約+詳細**(`...frontrunner: Trey Gowdy`)
- 引用符入りは「発言を先頭に置く」型: `'It's a stone around your neck': Arizona Republicans...`
- `after`(結果→原因)と `as`(同時進行)が頻出

## 8. 【重点】画像なしで成立している設計

当社は著作権上、記事に写真を持てない。**画像ゼロで運営している実例2つ**:

### text.npr.org(HTML全体わずか6,041バイト)
- 一覧は**見出しだけを24本、縦一列。要約なし・時刻なし・画像なし**。冒頭に日付1行のみ
- 記事: パンくず → 見出し → `By Rafael Nam` → 日時 → 本文。装飾ゼロ
- 関連記事は `Related Story: NPR` という**テキスト1行**だけ
- 動画も見出しに `Video:` を前置して文章化

### lite.cnn.com
- `CNN` / `7/25/2026` / `Latest Stories` の3行 → **見出しのみ100本を一列**。カテゴリ区切りなし、**順序だけが優先度**
- 「見出しだけで意味が完結する」前提のため、**見出しが長め**:
  `Singer d4vd's preliminary hearing sheds new light on the investigation into teen girl's killing. Here are the takeaways`

### 画像の代わりに何を視覚アンカーにしているか
| 媒体 | 代替手段 |
|---|---|
| Axios | **タイポグラフィ**(太字ラベル+箇条書き)でスキャン可能性を担保。絵文字は💭1個だけ意図的に |
| Semafor | **構造そのものが視覚要素**(The News / Know More / Room for Disagreement) |
| AP | **`5 MIN READ`とコメント数の数字**が視覚アンカー |
| BBC | `Most read` を**1〜10の番号付き見出しのみ**で密度の高いブロックに |
| Al Jazeera | `list 1 of 10` の相対時刻付き見出し連打で「生きている感じ」を出す |

## 9. 当社が真似できる設計要素(優先度順10)

1. **リードは1段落・150〜240字で結論を言い切る**(全社が収束している唯一の共通点。AI生成でも最も破綻しにくく効果が最大)
2. **Axios式の太字ラベルを日本語化**: `なぜ重要か:` `きっかけ:` `全体像:` `行間を読む:` `要点:` `反対の見方:` `数字で見る:` `次の注目点:` の8種程度
3. **全リンクに所要時間を表示**(「2分で読める」)。**数字が画像の代わりの視覚アンカーになる**
4. **1つの出来事を「ハブ名+切り口4本」で入口を作る**。AI生成は同一素材から複数の切り口を量産しやすく**最も相性が良い**
5. **見出しは能動態・現在形・25〜40字**。「〇〇が△△を発表」→「〇〇、△△を発表」で語数を削る。ラベルは見出しの外に(`解説:` `独自:` `検証:`)
6. **要約文(dek)を必ず1文・110〜140字**。トップを「要約あり/見出しのみ」の2層に分けると画像なしでも階層が作れる
7. **相対時刻+絶対時刻の二重表示。更新記事は「公開」と「更新」を必ず併記**
8. **本文中に関連記事をテキスト1行で差し込む**(最も低コストな回遊手段)
9. **タグを「大分類/出来事名/地名/人名/組織」の5層で多重に**。継続中の出来事名を常設カテゴリに昇格。AIならタグ抽出は自動化でき、**人力メディアより有利に作れる部分**
10. **Semaforの「事実/自社の見立て/反対意見」の3分割を、AI生成の信頼性担保として使う**。
    AI生成記事は「意見と事実の境界が曖昧」という批判を受けやすいため、**構造で分離しておくことが最大の防御**。
    加えて `This story has been updated with ...` のような**更新履歴を本文末に平文で書く慣行**も採用する

---
※Reuters(401)とBloombergは一切観察できていないため上記に含まれない。
※Axios/Politico/Quartz/Business Insiderは記事本文と見出しのみRSS実データ、**トップページの情報設計は未観察**。
