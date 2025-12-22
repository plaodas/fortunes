# litellm Docker セットアップ

このリポジトリに litellm をインストールした Docker コンテナを追加しました。


統合済みのビルドと起動:

```bash
docker compose up --build -d
```

コンテナに入って `litellm` を確認する (コンテナ名は `fortunes_litellm`):

```bash
docker exec -it fortunes_litellm sh
litellm --help
```

注記:
- このイメージは `litellm` を pip でインストールしています。まずは `litellm --help` で利用可能なコマンドを確認してください。
- サーバとしての起動方法などは `litellm` のドキュメントに依存します。必要ならこのイメージに起動コマンドを追加します。
