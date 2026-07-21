# AI TECH TIMES — AIニュースサイト自動運営会社

会社概要・役員・業務フローは COMPANY.md を参照。

## 構成

- `run_pipeline.py` — フルパイプライン(カテゴリ別収集→選定→執筆→バズ集計→サイト生成→X告知)
- `src/collect.py` — カテゴリ別RSS巡回(標準ライブラリのみ)。カテゴリ/ソース追加は `CATEGORIES` と `SOURCES`
- `src/editor.py` — Gemini `gemini-flash-latest`(無料枠)で選定+執筆+バズコメント。RESTを直叩き、SDK依存なし。本数は `PICKS_PER_CATEGORY`
- `src/buzz.py` — YouTube Data API(急上昇×6地域)で世界バズ動画TOP10集計 → `data/buzz.json`。`YOUTUBE_API_KEY` 未設定ならスキップ
- `src/build.py` — `data/` → `docs/` に静的サイト全再生成(カテゴリ別ページ+buzz.html+JSON-LD/OGP/sitemap/llms.txt/RSS/robots)
- `src/announce.py` — X告知。4つのXトークンsecretsが全部あるときだけ投稿、なければスキップ
- `.github/workflows/daily.yml` — 1日4回cron(朝7:00/昼12:30/夕方17:30/夜21:30 JST)。data/とdocs/をcommit&push

## 運用ルール

- 配信は **Cloudflare Pages**(https://ai-tech-times.pages.dev、Git連携でmainのdocs/を自動デプロイ、ビルドコマンドなし)。BANKSY系と切り離すため banksy-s2.github.io のGitHub Pagesは使わない
- Secrets登録はWindowsではパイプ禁止、必ず `gh secret set NAME --body "値"`(CR混入で401)
- Geminiは `src/editor.py` の `MODELS` チェーン(lite→2.5-flash→flash-latest)で自動フォールバック。flash-latest(=3.5-flash)は無料枠20回/日しかないので主力はlite
- ローカルテスト: `$env:GEMINI_API_KEY="..."; python run_pipeline.py`(X未設定なら告知だけスキップされる)
- 記事データは `data/articles.json` に全件蓄積、`data/posted_urls.json` が既報URLの重複防止台帳
