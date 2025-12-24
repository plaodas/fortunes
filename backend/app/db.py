import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to PostgreSQL for this project. If an env var is provided it will be
# used; also normalize legacy `postgres://` scheme to the SQLAlchemy
# `postgresql+psycopg2://` form so both Docker and local URLs work.

default = "postgresql+psycopg2://postgres:password@localhost:5432/fortunes"
DATABASE_URL = os.getenv("DATABASE_URL", default)

# Normalize common postgres scheme
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True, echo=(os.getenv("SQLALCHEMY_ECHO") == "1"))
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
