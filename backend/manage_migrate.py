"""Simple migration runner for the backend migrations/init.sql

Usage:
  python manage_migrate.py

This will use the `DATABASE_URL` environment variable (same as the app).
"""

import asyncio
import os

from app import db
from sqlalchemy.ext.asyncio import AsyncConnection


def _migration_path(file_name: str) -> str:
    migrations_file = os.path.join(os.path.dirname(__file__), "backend", "migrations", file_name)
    # support running both from repo root and from backend folder
    if not os.path.exists(migrations_file):
        migrations_file = os.path.join(os.path.dirname(__file__), "migrations", file_name)
    return migrations_file


async def _run_migration(conn: AsyncConnection, file_name: str) -> None:
    migrations_file = _migration_path(file_name)

    if not os.path.exists(migrations_file):
        print("No migrations file found at expected location.")
        return

    with open(migrations_file, "r", encoding="utf-8") as f:
        sql = f.read()

    # Some DBAPIs (asyncpg) reject executing multiple statements in a
    # single prepared statement. Execute statements one-by-one to avoid
    # the "multiple commands in a prepared statement" error.
    # This is a simple splitter: it splits on semicolons. It works for
    # typical migration files that use semicolons only to terminate
    # statements. If your SQL contains semicolons inside string literals
    # or dollar-quoted blocks, consider using a more robust parser or
    # running the file with the `psql` client.
    parts = [p.strip() for p in sql.split(";")]
    for part in parts:
        if not part:
            continue
        # append semicolon to keep statements identical
        stmt = part + ";"
        await conn.exec_driver_sql(stmt)


async def run_migrations_async(files: list[str]) -> None:
    try:
        async with db.engine.begin() as conn:
            for file_name in files:
                await _run_migration(conn, file_name)

        print("Migrations applied successfully.")
    except Exception as e:
        print("Failed to apply migrations:", e)


def run_migrations(files: list[str]) -> None:
    asyncio.run(run_migrations_async(files))


if __name__ == "__main__":
    run_migrations(["init.sql", "02_create_users.sql"])
