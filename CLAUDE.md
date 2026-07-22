# AI TECH TIMES — AIニュースサイト自動運営会社(引き継ぎ書)

新しいセッション/別モデル(Opus等)はまずこれを全部読むこと。会社概要・役員は COMPANY.md。

## これは何か

総合ニュースサイト https://ai-tech-times.web.app/ を**このPC上で全自動運営**する会社。
毎時00分にWindowsタスクスケジューラ「**AI-Tech-Times-Edition**」が `run_edition.ps1` を実行し、
記事生成→サイト再生成→git push→Firebaseデプロイまで無人で回る。**Claudeは日常運転には不要**(会話時のみ登場)。

- フル便(7/12/17/21時): 全6カテゴリ10本+X告知
- 軽量便(他の毎時): 1カテゴリ順繰りで1〜2本(`run_pipeline.py` の `MAIN_HOURS` と hour%6 ローテ)
- バズ動画TOP10は**毎便(毎時)更新**。コメントは新規ランクイン分だけGemini生成(既存は引き継ぎ)
- 新ネタが全部既報なら「新着なし(正常)」で終わるのが仕様。無理に書かない

## 構成

- `run_edition.ps1` — 実行の入口(鍵読込→pipeline→push→deploy)。**変更時の鉄則は下記「地雷」参照**
- `run_pipeline.py` — 便の本体。フル/軽量の分岐、日報、status.json更新
- `src/collect.py` — カテゴリ別RSS収集。重複排除は3層: URL完全一致 / 正規化タイトル一致 / **文字バイグラム類似0.5以上**(`_is_dup_topic`)
- `src/editor.py` — Gemini呼び出し。**モデルチェーン** `MODELS`(lite→2.5-flash→flash-latest)、429の`PerDay`検知で即次モデルへ。選定は2.5-flash優先。記事は**保存前スキーマ検証**あり
- `src/build.py` — `data/` → `docs/` 静的サイト全再生成。SEOタイトルは`INDEX_TITLE`/`CATEGORY_SEO`
- `src/buzz.py` — YouTube急上昇6地域→世界バズTOP10
- `src/announce.py` — X告知(おっちゃん垢@ganmenmahi1020)。**URLを本文に入れない**(URL入りは$0.20/回、無しは$0.015)
- `src/report.py` — 日報(company/reports/)とライブ用status.json
- `src/storage.py` — **全JSON保存はこれ経由**(アトミック書込+.bak復旧)。直接write_text禁止
- `docs/office.html` — 編集部ライブ(擬人化オフィス)。pipelineとは独立、build対象外
- `register_task.ps1` — スケジュール登録(24個のdailyトリガー)。変更したらユーザーに「ニュース自動化ON(ダブルクリック).bat」を再実行してもらう(schtasks系はClaudeから実行不可=クラシファイアブロック)

## 地雷一覧(2026-07-21に実際に踏んだもの。厳守)

1. **.ps1/.batは純ASCIIのみ**。日本語コメント1行でPS5.1がANSI解釈して構文崩壊→タスクが0x1即死する(2回発生)。
   検査: `grep -c '[^ -~]' run_edition.ps1` が0であること。変更後は必ず
   `powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File run_edition.ps1 -NoPost` で実走確認
2. **監視にtail -fを使わない**。Windowsではログを書込ロックして本番のAdd-Contentを壊す。しかもTaskStop後に孤児tail.exeが残り続ける(`tasklist | grep tail` で確認・taskkill)。監視するならgitコミットのポーリング方式
3. **Gemini無料枠**: `gemini-flash-latest`(=3.5-flash)は**20回/日しかない**。主力はlite。日次リセットは**16:00 JST**。クォータはモデル別に独立
4. **JSONを素のwrite_textで保存しない**(破損→全便連鎖クラッシュの元)。必ず`storage.save_json`
5. **gh secret set / schtasks登録 / APIキーを含むコマンドはClaudeから実行不可**(自動ブロック)。ユーザーにダブルクリック用batを作って渡す方式(過去bat: finish_setup.ps1, register_task.ps1)
6. **タイトル・数値の捏造ガード**: 記事は元記事要約にある事実のみ。AIのリライト提案が事実にない数字を足した実例あり。疑わしければ却下
7. HTMLキャッシュはno-cache設定済(firebase.json)。「古い画面が見える」と言われたら開き直し案内
8. Windowsのコンソール出力はcp932。Pythonは`PYTHONIOENCODING=utf-8`、`sys.stdout.reconfigure`済み

## 鍵の場所(ローカル.envから実行時に読む。どこにも登録しない)

- GEMINI_API_KEY → `Desktop\explainer-studio\.env`
- YOUTUBE_API_KEY → `Desktop\youtube-ai-studio\.env`
- X 4種 → `Desktop\_Projects\kane-kizuki-bot\.env` — **ただし2026-07-21時点で失効(401)**。6/12再発行時にローカル未更新。X告知を生かすにはユーザーがdeveloper.x.comで再取得必要

## 運用コマンド(手動)

- 便を今すぐ回す: `powershell -NoProfile -ExecutionPolicy Bypass -File run_edition.ps1`(投稿なしテストは `-NoPost`)
- デプロイのみ: `firebase deploy --only hosting --project ai-tech-times --non-interactive`
- タスク状態: `powershell -Command "Get-ScheduledTaskInfo -TaskName 'AI-Tech-Times-Edition'"`(LastTaskResultが0以外=失敗)
- ログ: `logs/run.log`(2MBでローテ)、`logs/deploy-last.log`、緊急時`logs/run-fallback.log`

## 会社としての運営

- **窓口は統括秘書・白瀬凪**(人格: `company/SECRETARY.md` ※リポジトリ同梱。PC原本は`Desktop\new-company\secretary.md`)。役員たちは凪の部下として登場
- **スマホ/クラウドセッション対応**: このリポジトリはPC外(claude.ai/code等)からも開かれる。その場合 `company/SECRETARY.md` の「セッション環境による分担」に従う — 会議・提案・コード/記事ルール編集のcommit&pushはOK、`data/`編集とデプロイ・鍵の操作はNG。pushすればPCの毎時便が `git pull --rebase` で自動反映(最大1時間)
- 「編集会議」と言われたら: `company/reports/`の日報と実データを読み、役員ロールプレイで議論→議事録を`company/meetings/`に保存。**会議はロールプレイであることを社長は了解済み。誇張しない(「噓偽りなく」が社訓)**
- 提案は`company/proposals/`。課金・公開・後戻り困難な操作は必ず社長承認
- 未決事項(2026-07-21時点): Xトークン再取得 / Search Console / GA4 / 固定ポスト / 会議決定D1〜D6(3行まとめ・週刊TOP10・トップ記事大型表示・はてブ追加・OGP画像・監査残3件)

## GitHub Actions(休止中)

`.github/workflows/daily.yml` のcronはコメントアウト済(ローカル実行と二重化するため)。
クラウドに戻すにはSecrets6種登録+cron復活。GitHub Pagesは無効化済(BANKSYアカウント名を出さないため)
