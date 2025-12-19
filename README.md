# Fortunes (MVP)

This repository contains a minimal scaffold for the Fortunes MVP.

Quick start (requires Docker):

```bash
# from repo root
docker compose up --build

# frontend: http://localhost:3000
# backend: http://localhost:8000
```

Backend endpoint:
- POST /analyze  (JSON: {name, birth_date, birth_hour})
