"""Simple migration runner for the backend migrations/init.sql

Usage:
  python manage_migrate.py

This will use the `DATABASE_URL` environment variable (same as the app).
"""

import os

from app import db


def run_migrations():
    migrations_file = os.path.join(
        os.path.dirname(__file__), "backend", "migrations", "init.sql"
    )
    # support running both from repo root and from backend folder
    if not os.path.exists(migrations_file):
        migrations_file = os.path.join(
            os.path.dirname(__file__), "migrations", "init.sql"
        )

    if not os.path.exists(migrations_file):
        print("No migrations file found at expected location.")
        return

    with open(migrations_file, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        with db.engine.begin() as conn:
            conn.exec_driver_sql(sql)
        print("Migrations applied successfully.")
    except Exception as e:
        print("Failed to apply migrations:", e)


if __name__ == "__main__":
    run_migrations()
