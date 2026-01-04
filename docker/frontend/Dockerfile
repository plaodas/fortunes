# --- Build Stage ---
FROM node:18-alpine AS builder

WORKDIR /app

# 依存関係だけ先にコピー（キャッシュ効率UP）
COPY package*.json ./

# devDependencies を含めてビルドに必要なものだけインストール
RUN npm ci

# アプリ本体をコピー
COPY . .

# 本番ビルド
RUN npm run build

# --- Production Stage ---
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# 本番に必要なファイルだけコピー
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Next.js の画像最適化を無効化（軽量化）
ENV NEXT_DISABLE_IMAGE_OPTIMIZATION=1

EXPOSE 3000

CMD ["npm", "start"]
