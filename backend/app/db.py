import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Default to PostgreSQL for this project. If an env var is provided it will be
# used. For async SQLAlchemy we use the `asyncpg` driver (postgresql+asyncpg).
default = "postgresql+asyncpg://postgres:password@localhost:5432/fortunes"
DATABASE_URL = os.getenv("DATABASE_URL", default)

# Normalize common postgres schemes to asyncpg form so both Docker and local URLs work.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif "psycopg2" in DATABASE_URL and "asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "asyncpg")

# Async engine and sessionmaker
engine = create_async_engine(DATABASE_URL, future=True, echo=(os.getenv("SQLALCHEMY_ECHO") == "1"))
SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
