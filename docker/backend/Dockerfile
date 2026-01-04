FROM python:3.11-slim

WORKDIR /app

# Python の最適化
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 必要な OS パッケージだけ入れる
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 依存関係を先にコピー（キャッシュ効率UP）
COPY requirements.txt .

# 軽量インストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体をコピー
COPY . /app

EXPOSE 8000

# Uvicorn を軽量設定で起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "warning"]
