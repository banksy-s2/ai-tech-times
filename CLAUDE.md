# AI TECH TIMES — AIニュースサイト自動運営会社

会社概要・役員・業務フローは COMPANY.md を参照。

## 構成

- `run_pipeline.py` — フルパイプライン(カテゴリ別収集→選定→執筆→バズ集計→サイト生成→X告知)
- `src/collect.py` — カテゴリ別RSS巡回(標準ライブラリのみ)。カテゴリ/ソース追加は `CATEGORIES` と `SOURCES`
- `src/editor.py` — Gemini `gemini-flash-latest`(無料枠)で選定+執筆+バズコメント。RESTを直叩き、SDK依存なし。本数は `PICKS_PER_CATEGORY`
- `src/buzz.py` — YouTube Data API(急上昇×6地域)で世界バズ動画TOP10集計 → `data/buzz.json`。`YOUTUBE_API_KEY` 未設定ならスキップ
- `src/build.py` — `data/` → `docs/` に静的サイト全再生成(カテゴリ別ページ+buzz.html+JSON-LD/OGP/sitemap/llms.txt/RSS/robots)
- `src/announce.py` — X告知。4つのXトークンsecretsが全部あるときだけ投稿、なければスキップ
- `.github/workflows/daily.yml` — 毎朝7:00 JST(22:00 UTC)cron。data/とdocs/をcommit&push

## 運用ルール

- GitHub Pagesは main ブランチの /docs から配信
- Secrets登録はWindowsではパイプ禁止、必ず `gh secret set NAME --body "値"`(CR混入で401)
- Geminiモデルは `gemini-flash-latest` 固定(他は無料枠で429)
- ローカルテスト: `$env:GEMINI_API_KEY="..."; python run_pipeline.py`(X未設定なら告知だけスキップされる)
- 記事データは `data/articles.json` に全件蓄積、`data/posted_urls.json` が既報URLの重複防止台帳
