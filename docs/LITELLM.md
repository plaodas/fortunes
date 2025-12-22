# litellm Docker セットアップ

このリポジトリに litellm をインストールした Docker コンテナを追加しました。


統合済みのビルドと起動:

```bash
docker compose up --build -d
```

プロバイダー切替（OpenAI / Gemini / DeepSeek）

1) サンプル env ファイルを編集して API キーを設定します（`litellm` に用意済み）:

- `litellm/env_all.env`

選んだ env ファイルを使って起動する場合:

```bash
docker compose --env-file litellm/env_openai.env up --build -d
```

2) コンテナで状態確認:

```bash
docker logs -f fortunes_litellm
docker exec -it fortunes_litellm sh
litellm --help
```

注意:
- Gemini（Google）は通常 `GOOGLE_APPLICATION_CREDENTIALS` でサービスアカウント JSON を指定します。コンテナにマウントしてパスを設定してください。
- `litellm` を使うアプリ側では、環境変数 `LITELLM_PROVIDER` を読み取り、該当プロバイダー名で `litellm` を初期化してください。

マウント手順（Google / Gemini 用サービスアカウント JSON）

1. ホスト上で secrets ディレクトリを作り、サービスアカウント JSON を配置します（このファイルは必ず `.gitignore` に入れてください）:

```bash
mkdir -p ./secrets
cp /path/to/your-google-service-account.json ./secrets/google-service-account.json
chmod 400 ./secrets/google-service-account.json
```

2. `docker compose up` で起動すると `docker-compose.yml` 側でファイルをコンテナ内 `/secrets/google-service-account.json` にマウントし、環境変数 `GOOGLE_APPLICATION_CREDENTIALS` が自動で設定されます。

```bash
docker compose up --build -d
```

3. コンテナ内で `GOOGLE_APPLICATION_CREDENTIALS` を参照する SDK（例: `google-cloud-aiplatform`）はそのパスで認証を行います。

注意:
- ファイルが存在しない場合はコンテナは起動しますが、Gemini 呼び出しの段で認証エラーになります。ファイルのパスと権限を確認してください。
- セキュリティのためファイルは読み取り専用でマウントしています（`:ro`）。

