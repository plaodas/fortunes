"""Simple migration runner for the backend migrations/init.sql

Usage:
  python manage_migrate.py

This will use the `DATABASE_URL` environment variable (same as the app).
"""

import os

from app import db
from sqlalchemy import Connection


def _run_migration(conn: Connection, file_name: str):
    migrations_file = os.path.join(
        os.path.dirname(__file__), "backend", "migrations", file_name
    )
    # support running both from repo root and from backend folder
    if not os.path.exists(migrations_file):
        migrations_file = os.path.join(
            os.path.dirname(__file__), "migrations", file_name
        )

    if not os.path.exists(migrations_file):
        print("No migrations file found at expected location.")
        return

    with open(migrations_file, "r", encoding="utf-8") as f:
        sql = f.read()

    conn.exec_driver_sql(sql)


def run_migrations(files: list[str] = None):
    try:
        with db.engine.begin() as conn:
            for file_name in files:
                _run_migration(conn, file_name)

        print("Migrations applied successfully.")
    except Exception as e:
        print("Failed to apply migrations:", e)


if __name__ == "__main__":
    run_migrations(
        [
            "init.sql",
            "kanji.sql",
        ]
    )
