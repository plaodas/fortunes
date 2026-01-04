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
ENV PORT=3000

# 本番に必要なファイルだけコピー
# node ユーザを利用（公式イメージに 'node' がいる）
# ビルド成果をコピーして所有権を node にする
COPY --from=builder /app/package*.json ./
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/.next ./.next
COPY --from=builder --chown=node:node /app/public ./public

# COPY --chown が使えない場合コピー後に chown を実行（要 root）
# COPY --from=builder /app /app
# RUN chown -R node:node /app
# USER node

# Next.js の画像最適化を無効化（軽量化）
ENV NEXT_DISABLE_IMAGE_OPTIMIZATION=1

EXPOSE 3000

CMD ["npm", "start"]
