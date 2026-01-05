import os
from typing import Any, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# Default to PostgreSQL for this project. If an env var is provided it will be
# used. For async SQLAlchemy we use the `asyncpg` driver (postgresql+asyncpg).
default = "postgresql+asyncpg://postgres:password@localhost:5432/fortunes"
DATABASE_URL = os.getenv("DATABASE_URL", default)

# Normalize common postgres schemes to asyncpg form so both Docker and local URLs work.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Async engine and sessionmaker
_engine: Optional[AsyncEngine] = None
_SessionLocal: Optional[async_sessionmaker[AsyncSession]] = None
Base = declarative_base()


def _ensure_engine_and_maker() -> None:
    """Lazily create the async engine and sessionmaker on first use.

    Creating the engine lazily ensures it's created on the currently running
    event loop. This avoids asyncpg errors when tests or ASGI transports run
    with different event loops than the module import time loop.
    """
    global _engine, _SessionLocal
    if _engine is None:
        # Default to using NullPool to avoid cross-event-loop connection
        # issues in test and short-lived invocation environments. Set
        # DB_USE_NULLPOOL=0 (or false) to enable pooled connections.
        use_null = os.getenv("DB_USE_NULLPOOL", "1").lower() in ("1", "true", "yes")

        engine_kwargs: dict = {
            "future": True,
            "echo": (os.getenv("SQLALCHEMY_ECHO") == "1"),
            "pool_pre_ping": True,
        }

        if use_null:
            engine_kwargs["poolclass"] = NullPool
        else:
            # Allow tuning pool size via env; sensible defaults kept.
            engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "5"))
            engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "0"))

        _engine = create_async_engine(DATABASE_URL, **engine_kwargs)
        _SessionLocal = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


def SessionLocal() -> AsyncSession:
    """Return a new `AsyncSession` instance.

    This is intentionally a function (not an already-created sessionmaker)
    so callers like `async with SessionLocal() as session:` continue to work
    while the engine and maker are created lazily on the active loop.
    """
    _ensure_engine_and_maker()
    assert _SessionLocal is not None
    return _SessionLocal()


async def get_db() -> AsyncGenerator[Any, Any]:
    async with SessionLocal() as session:
        yield session


# Provide a module-level `engine` object for tests that call
# `engine.sync_engine.dispose()` after using `asyncio.run()`. The real
# async engine is created lazily; when `dispose()` is called we attempt to
# dispose the underlying engine's sync_engine if it exists.
class _SyncEngineDisposer:
    def dispose(self) -> None:
        try:
            if _engine is not None:
                _engine.sync_engine.dispose()
        except Exception:
            # swallowing exceptions here matches existing test behaviour
            # where dispose is called in a try/except block.
            pass


class _EngineProxy:
    def __init__(self) -> None:
        self.sync_engine = _SyncEngineDisposer()


# Export `engine` so tests importing `from app.db import engine` succeed.
engine = _EngineProxy()
