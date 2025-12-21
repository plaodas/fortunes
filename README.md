# Fortunes (MVP)

This repository contains a minimal scaffold for the Fortunes MVP.

Quick start (requires Docker):

```bash
# from repo root
docker compose up --build

# DBのマイグレーション
PYTHONPATH=./backend python backend/manage_migrate.py # テーブル作成
psql "$DATABASE_URL" -f backend/migrations/kanji_data.dump.sql # dumpファイルをインポート

# frontend: http://localhost:3000
# backend: http://localhost:8000

```

- 開発環境用
```
pip install -r dev-requirements.txt
```

## 漢字の画数DBについて
漢字の画数は[漢字画数データベース](https://kanji-database.sourceforge.net/database/strokes.html)からダウンロードさせていただきました。

- ファイル：backend/migrations/ucs-strokes.txt,v
- 漢字画数インポート方法
  `PYTHONPATH=./backend python backend/import_kanji.py`



Backend endpoint:
- POST /analyze  (JSON: {name, birth_date, birth_hour})



