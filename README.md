# 🌟四柱推命と姓名判断から人生のブループリントを読み解くアプリ (MVP)

# 概要
四柱推命と姓名判断からあなたの人生のブループリントを物語風に読み解くアプリです。

「名前」、「生まれた年月日時」を入力すると命式、五行、五格が計算されて大まかな人生の流れが桃源郷の旅路を模した物語で表現されます。

算出は一般的なものを更に簡略化しています。算出した値からLLMで鑑定文を作成します。

AI駆動開発の練習用です。
認証、厳密なバリデーション、ログ監視などは未実装です。


### 画面イメージ

<img src="images/preview1.png" height="400"><img src="images/preview2.png" height="400"><img src="images/preview4.png" height="400"><img src="images/preview5.png" height="400">

<img src="images/preview6.png" height="400"><img src="images/preview7.png" height="400">

# 構成
コンテナは以下のような構成です
- frontend: node, react, next
- backend: python, fastapi
- worker: python, arq
- redis: redis
- db: poatgresql

```mermaid
flowchart TD
  %% ノード定義
  user("`ユーザー
    (ブラウザ / スマホ)
  `")
  subgraph 開発対象
    frontend["`frontend（React/Next.js）
      🔵氏名、誕生日、出生時刻の入力
      🔵結果の表示
      🔵鑑定履歴の表示
    `"]
    backend["`backend（FastAPI）
      🔵ドメインロジック：
        命式計算、五行、五格
      🔵LiteLLM用のプロンプト生成
      🔵鑑定結果生成
    `"]
    worker["`worker（arq）
      🔵ジョブキュー管理
    `"]
    redis["`redis
      🔵ジョブ情報保存
    `"]
    db["`db（postgresql）
      🔵鑑定履歴保存
    `"]
  end
  openai("OpenAI API")
  google("Google Gemini API")
  monitor("`[未実装] 監視・ログ
    APIレスポンス時間/エラー率
    モデル別コスト／トークン使用量
    （Grafana/Loki/CloudWatch等）
  `")

  user <-->|認証は後回し| frontend
  frontend <--> backend
  backend <--> worker
  worker <--> redis
  backend <--> db
  backend --> monitor
  backend <--> openai
  backend <--> google

  %% 幅を指定するクラス定義（pxで指定）

  classDef wideCard stroke:#333,stroke-width:1px
  class * wideCard
  classDef dev fill:#fff,stroke:#333,stroke-width:2px,width:400px;text-align:center
  class frontend,backend,worker,redis,db dev

```


## 設定方法

### APIキー 設定
1. [Google AI Studio](https://aistudio.google.com/)でAPI keyを取得してください。
2. REPOルートの`.env.sample`を`.env`にファイル名変更
3. `GEMINI_API_KEY=`に `1.` で取得したキーをコピーして貼り付けます

### コンテナ起動、マイグレーション
```bash
# from repo root
docker compose up --build -d

# DBのマイグレーション
# "$DATABASE_URL"はご自身の環境に合わせて修正してください
DATABASE_URL="postgresql://postgres:password@localhost:5432/fortunes"
psql -v -d "$DATABASE_URL" -f backend/migrations/init.sql

# 漢字データ
BACKUP_PATH="backend/migrations/kanji.dump"
pg_restore -v -d "$DATABASE_URL" --clean --no-owner --no-privileges "$BACKUP_PATH"
```
PostgreSQLのlocale：ja_JP.UTF-8、futuresデータベースの collationも'ja_JP.UTF-8'で指定。
誕生日時は内部でUTCとして保存し、指定されたtimezoneに戻して返しています。


### ブラウザアクセス

`http://localhost:3000`
で画面が表示されます

### LLMのモデル

鑑定文作成とサマリ作成で使用するモデルを分けています。
- 鑑定文作成： gemini-2.5-flash
- サマリ作成： gemini-2.5-flash-lite

鑑定文は表現力が必要なので、`gemini-2.5-pro`やOpenAIの`GPT-4o`のようなモデルがおすすめです。この環境では無料枠があるgemini-2.5-flashを使用しています。
サマリ作成は表現力が問われないので、`gemini-2.5-flash-lite`のような軽くて安価なモデルがよいです。

プロンプトも[鑑定文](backend/app/services/prompts/template_life_analysis.py)と[サマリ](backend/app/services/prompts/template_life_analysis_summary.py)で分けています


### 開発環境用ツールのインストール
- リンター、コードフォーマッターを使用しています

```
pip install -r dev-requirements.txt
```

### TEST
テストコマンド

```bash
docker compose exec frontend npm test -- --coverage --coverageDirectory=coverage --coverageReporters=text
docker compose exec backend bash -c "PYTHONPATH=/app pytest"
```

### debug
uvicornとsqlalchemyのdebugを有効化
```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up --build
```




## 永続運用
<!-- ### 運用(systemd)： -->
 <!-- Service Unit (推奨): docker compose プロジェクト全体を systemd で管理するのが簡単で堅牢 -->
<!-- ```
[Unit]
Description=Fortunes Docker Compose
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/agake/work/fortunes
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
``` -->
<!-- 個別コンテナ管理: もし worker のみ永続化したければ ExecStart=/usr/bin/docker compose up -d worker を使う。
注意: ユーザー単位で動かす場合は user-level systemd も可。systemd の Restart= ポリシーや StartLimitBurst で再起動制御。 -->

### ログ
- ローテーション
  - `docker-compose.yml`の`logging:`で設定
<!-- 集中ログ基盤: Loki/Promtail, ELK (Elasticsearch/Logstash/Kibana), Fluentd/Graylog などへ送るのが推奨（検索とアラートが容易）。
エラートラッキング: Sentry を導入して例外トレースを収集。Worker/Server に SDK を入れるだけでOK。
ログ保持方針: 法令や容量に合わせて保管期間を決め、古いログは圧縮/削除。 -->

<!-- ### 監視（メトリクス・アラート）: -->

<!-- メトリクス収集: Prometheus + Grafana。アプリ側に /metrics を公開（FastAPI に prometheus_client または fastapi-prometheus を導入）。
重要な指標:
job queue length（Redis の待ち行列長）
job failure rate / error count（Worker）
job processing time（遅延検出）
Redisメモリ使用率、Postgres接続数、CPU/メモリコンテナリソース
サンプルアラート（PromQL）:
job失敗率 > 1% (5m)
Redis memory > 80%
job処理時間の95パーセンタイル > 30s
可視化: Grafana ダッシュボードでSLA指標と最近の失敗を表示。 -->

### ヘルスチェック / Liveness & Readiness:
 FastAPI に /health （Liveness）と /ready （Readiness 、DB・Redis接続チェック）を追加。Kubernetes での運用や systemd 側の監視で使う。


<!-- ### トレーシング & 分析: -->

<!-- 分散トレーシング: OpenTelemetry + Jaeger（LLM呼び出しや DB クエリの遅延調査に有効）。
サンプル: opentelemetry-instrumentation-fastapi を導入して自動計測。 -->

### 永続データ管理 / バックアップ:
```bash
# バックアップ backupディレクトリにfortunes-ooooooooooooooo.dumpで保存
scripts/backup_fortunes.sh

# レストア
scripts/restore_fortunes.sh backup/fortunes-ooooooooooooooo.dump
```
<!-- Postgres バックアップ: 定期的な pg_dump / WAL アーカイブ。自動化スクリプト + S3 などへの保存。
DB マイグレーション管理: alembic 等でスキーマ管理とリリース手順を確立。 -->

<!-- ### 運用オペレーション（通知・Runbook）: -->

<!-- アラート通知: Slack/Email/PagerDuty へ通知（Grafana/Alertmanager 経由）。
Runbook: 代表的問題（Redis接続切断、LLM APIキー切れ、DB接続枯渇）の復旧手順を文書化。
監査ログ: 主要操作（設定変更・deploy・DB restore）の記録。 -->

<!-- ### セキュリティ・設定管理: -->

<!-- 秘密管理: 環境変数を直接置かず Vault / AWS Secrets Manager 等で管理。
アクセス制御: DB/Redis のネットワークアクセスは内部ネットワークに限定。 -->



## その他
### (参考)ジョブのキュー管理 Arq backendコンテナで確認する
```bash
$ docker compose exec backend bash -lc "PYTHONPATH=/app  python -m app.worker"

07:57:07: Starting worker for 1 functions: app.tasks.process_analysis
07:57:07: redis_version=7.4.7 mem_usage=1.01M clients_connected=1 db_keys=0


$ curl -X POST http://localhost:8000/analyze/enqueue \
  -H "Content-Type: application/json" \
  -d '{"name_sei":"太","name_mei":"郎","birth_date":"1990-01-01","birth_hour":12, "birth_tz":"Asia/Tokyo"}'
```




## 漢字の画数DBについて
漢字の画数は[漢字画数データベース](https://kanji-database.sourceforge.net/database/strokes.html)からダウンロードさせていただきました。

- ファイル：backend/migrations/ucs-strokes.txt,v
- 漢字画数インポート方法
  `PYTHONPATH=./backend python backend/import_kanji.py`

