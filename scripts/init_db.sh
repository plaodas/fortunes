# docker compose exec backend bash -c "python manage_migrate.py"
# DATABASE_URL="postgresql://postgres:password@localhost:5432/fortunes"
# psql -d "$DATABASE_URL" -f backend/migrations/sample_data.sql
# BACKUP_PATH="backend/migrations/kanji.dump"
# pg_restore -v -d "$DATABASE_URL" --clean --no-owner --no-privileges "$BACKUP_PATH"

DATABASE_URL="postgresql://postgres:password@localhost:5432/fortunes"
psql -d "$DATABASE_URL" -f backend/migrations/init.sql

# サンプルデータ投入
psql -d "$DATABASE_URL" -f backend/migrations/sample_data.sql

# 漢字データ
BACKUP_PATH="backend/migrations/kanji.dump"
pg_restore -v -d "$DATABASE_URL" --clean --no-owner --no-privileges "$BACKUP_PATH"
