"""編集部ラボ(自社オウンドメディア記事)の静的ページ生成。

build.py の毎時再生成とは独立して動く単発スクリプト。
docs/lab/ 配下に出力する(_sweep_orphans の対象は articles/ogp/archive/term のみなので消されない)。

使い方: python tools/build_lab_pages.py
"""
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import build  # noqa: E402

BOOK_URL = "https://zenn.dev/aidecodelabjp/books/ai-automation-jitsuroku"
LAB_DIR = build.DOCS / "lab"

PROMO = (
    '<div class="book-promo" style="margin:28px 0">📘 この記事の詳細版を含む実録本『'
    f'<a href="{BOOK_URL}">実録・個人AI自動化 ─ 月数ドルで回し続ける5つのレシピと事故対応</a>'
    '』(Zenn・500円/1章無料)を公開しています。</div>'
)

PAGES = [
    {
        "slug": "xbot-serverless-design",
        "title": "GitHub ActionsだけでXの自動投稿botを作る — サーバー不要・月2ドル台の設計図",
        "desc": "X(旧Twitter)の自動投稿botをサーバーなしで運用する構成。GitHub Actionsのcronとステートレス選択だけで、月2ドル台・インフラ代0円。実運用で踏んだ罠まで公開。",
        "body": """
<h1>GitHub ActionsだけでXの自動投稿botを作る</h1>
<p class="lead">サーバー不要・月2ドル台の設計図</p>

<p>X(旧Twitter)の自動投稿botを、サーバーなし・GitHub Actionsだけで運用している。月のコストは約2.25ドルで、そのほぼ全てがX APIの従量課金。インフラ代は0円だ。</p>

<p>「bot 作り方」で検索するとVPSを借りる記事が今も出てくるが、毎日数回投稿する程度のbotにサーバーは要らない。ここでは実際に運用している構成の設計図を書く。</p>

<h2>全体像</h2>
<pre><code>[posts.json(投稿ストック)]
        │
[GitHub Actions (cron)] → [post.py] → [X API]</code></pre>

<p>登場人物は3つだけ。投稿文のストックを入れたJSONファイル、定時に起動するワークフロー、そして投稿処理を行う数十行のPythonスクリプト。データベースも管理画面もない。</p>

<h2>設計判断1: 投稿文は「その場で生成」せず「ストック」する</h2>
<p>AIでbotを作るというと、実行のたびにLLMで文章を生成する構成を想像しがちだが、私はやらない。理由は2つ。</p>
<p>1つ目は品質管理。生成して即投稿する構成では、事故った文章がそのまま世に出る。ストック方式なら事前にまとめて生成して全件目視できる。自動化するのは「投稿作業」であって「品質保証」ではない、というのが私の線引きだ。</p>
<p>2つ目はコスト。毎回LLMを呼ぶと課金が投稿回数に比例して読めなくなる。生成は月に数回まとめてやれば実質無料の範囲に収まる。</p>

<h2>設計判断2: 状態管理を持たない</h2>
<p>「どの投稿を使ったか」を記録するDBやファイルを持つと、その保存が失敗したときの考慮が必要になり複雑になる。私の構成では<strong>「起点日からの経過日数 % ストック本数」</strong>で今日の1本を決める。完全にステートレスで、何回実行しても同じ日は同じ投稿が選ばれる。壊れる状態が存在しないものは、壊れない。</p>
<pre><code>day_number = (today - EPOCH).days
post = pool[day_number % len(pool)]</code></pre>

<h2>設計判断3: 沈黙する失敗を作らない</h2>
<p>無人システムの最大の敵は「止まっていることに気づけない停止」だ。私のbotも一度、APIトークンの失効で静かに止まっていたことがある。以来、投稿失敗時はワークフローを明示的に失敗させ、通知が飛ぶようにしている。正常に動いた記録より、失敗の通知の方がずっと重要だ。</p>

<h2>コストの現実(2026年時点)</h2>
<p>X APIは従量課金制で、テキストのみの投稿は1回あたり約0.015ドル、<strong>URL入りは約0.20ドルと13倍</strong>に跳ねる。1日5投稿・テキストのみなら月約2.25ドル。宣伝リンクを毎回貼りたくなるが、コストが13倍になる価値があるかは冷静に判断した方がいい。</p>
<p>GitHub Actionsはこの規模なら無料枠で十分足りる。cronの起動時刻は混雑時に数十分ずれることがあるので、分単位の正確さが必要な用途には向かない。</p>

<h2>この構成の応用範囲</h2>
<p>「ストック生成 → cron実行 → ステートレス選択」の3点セットは、X以外にもそのまま使える。定期実行系の自動化の基本形として、最初に習得する価値がある骨格だと思っている。</p>
""",
    },
    {
        "slug": "failsafe-automation",
        "title": "本番データを消した日から、個人のAI自動化を作り直した — フェイルクローズ設計3原則",
        "desc": "自作の自動化で本番の売上データを消した実体験と、そこから確立した3つの安全設計。削除はフェイルクローズ、消す前に現物を見る、同型ミスの再発は仕組みの負け。",
        "body": """
<h1>本番データを消した日から、個人のAI自動化を作り直した</h1>
<p class="lead">フェイルクローズ設計3原則</p>

<p>個人でAI自動化システムをいくつも運用している。X自動投稿bot、解説動画の全自動生成、そしてこのサイト自体の毎時無人更新。どれも無料枠と月数ドルで回っていて、専用サーバーは1台もない。</p>

<p>……という話だけ書くと、よくある「作ってみた」記事になる。今日はその逆側を書きたい。私はこの運用の途中で、<strong>本番データベースの売上データを消し飛ばした</strong>ことがある。</p>

<h2>何が起きたか</h2>
<p>複数端末でデータを同期して使う業務アプリを運用していた。テストのつもりで実行した削除処理が、本番データに向いていた。同期の仕組みは優秀に働き、削除は即座に全端末へ行き渡った。</p>
<p>バックアップがあったので復旧はできた。だが問題はそこではない。<strong>削除を実行する瞬間、私は自分が何を消すのかを確認していなかった</strong>。ローカルの思い込みだけで、リモートの本物に破壊的操作を撃った。これは注意力の問題ではなく、設計の問題だ。</p>

<h2>原則1: 破壊的操作はフェイルクローズにする</h2>
<p>削除・上書き・置換を含む処理は「迷ったら実行しない側」に倒す。対象件数を先に数えて想定と違えば中断する。接続先のデフォルトは必ず開発環境側にする。うっかりの着地点が安全側になるよう、デフォルト値で守る。</p>

<h2>原則2: 消す前に、必ず現物を見る</h2>
<p>破壊的操作の直前に、対象の現在の状態(件数・最終更新・サンプル数件)を取得して表示するステップを挟む。「これから消すものは、本当に思っているそれか」を人間の記憶ではなくコードに確認させる。</p>

<h2>原則3: 同じ型のミスが二度起きたら、仕組みの負け</h2>
<p>「気をつける」は対策ではない。事故やヒヤリが出たら、その日のうちに同じ型を機械的に検知するチェックを書いて、実行フローの入口に置く。人間が思い出して実行するチェックは必ず忘れるので、忘れても走る場所に置く。</p>

<h2>無人化とは例外処理の設計のこと</h2>
<p>このサイトを完全無人にしたときに確信したことがある。正常系の自動化は誰でもできる。難しいのは、異常が起きたときに必ず次の3択のどれかに落ちるよう設計することだ。</p>
<ul>
<li><strong>自然回復する</strong>(その回はスキップ、次の回で追いつく)</li>
<li><strong>安全に止まる</strong>(データを壊す前に停止する)</li>
<li><strong>人間に通知が届く</strong>(沈黙して止まらない)</li>
</ul>
<p>この3択に落とし切れたシステムだけが「触らなくていいシステム」になる。</p>
""",
    },
]


def _index_body() -> str:
    e = html.escape
    items = "".join(
        f'<li style="margin:14px 0"><a href="{build.BASE_URL}/lab/{e(p["slug"], quote=True)}.html">{e(p["title"])}</a>'
        f'<div style="font-size:.85rem;color:var(--dim);margin-top:4px">{e(p["desc"])}</div></li>'
        for p in PAGES)
    return ('<h1>編集部ラボ</h1><p class="lead">当編集部そのものを動かしている自動化の設計を、'
            '実際に運用しているものだけ公開しています。</p>'
            f'<ul style="list-style:none;padding:0">{items}</ul>{PROMO}')


def main() -> None:
    LAB_DIR.mkdir(parents=True, exist_ok=True)
    written = []
    for p in PAGES:
        path = f"/lab/{p['slug']}.html"
        html_doc = build._page(p["title"], p["desc"], path, p["body"] + PROMO)
        (LAB_DIR / f"{p['slug']}.html").write_text(html_doc, encoding="utf-8")
        written.append(path)
    idx = build._page("編集部ラボ — AI TECH TIMES", "AI TECH TIMES編集部の自動化設計を公開",
                      "/lab/", _index_body())
    (LAB_DIR / "index.html").write_text(idx, encoding="utf-8")
    written.append("/lab/")
    print("[lab] 生成:", ", ".join(written))


if __name__ == "__main__":
    main()
