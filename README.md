# Fortunes (MVP)

This repository contains a minimal scaffold for the Fortunes MVP.

Quick start (requires Docker):

```bash
# from repo root
docker compose up --build

# DBのマイグレーション
PYTHONPATH=./backend python backend/manage_migrate.py

# frontend: http://localhost:3000
# backend: http://localhost:8000

```

Backend endpoint:
- POST /analyze  (JSON: {name, birth_date, birth_hour})

開発環境に
```
pip install -r dev-requirements.txt
```
