from datetime import datetime

from sqlalchemy import JSON, TIMESTAMP, Boolean, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column  # mypy の推論を利用するためmapped_columnを使用
from sqlalchemy.sql import func

from .db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    birth_datetime: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    birth_tz: Mapped[str] = mapped_column(Text, nullable=False)
    result_birth: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_name: Mapped[dict] = mapped_column(JSON, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class Kanji(Base):
    __tablename__ = "kanji"

    char: Mapped[str] = mapped_column(Text, primary_key=True)
    codepoint: Mapped[str] = mapped_column(Text, nullable=False)
    strokes_text: Mapped[str] = mapped_column(Text, nullable=True)
    strokes_min: Mapped[int] = mapped_column(Integer, nullable=True)
    strokes_max: Mapped[int] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(Text, nullable=True)


class LLMResponse(Base):
    __tablename__ = "llm_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request_id: Mapped[str] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(Text, nullable=True)
    model_version: Mapped[str] = mapped_column(Text, nullable=True)
    response_id: Mapped[str] = mapped_column(Text, nullable=True)
    prompt_hash: Mapped[str] = mapped_column(Text, nullable=True)
    response_text: Mapped[str] = mapped_column(Text, nullable=True)
    usage: Mapped[dict] = mapped_column(JSON, nullable=True)
    raw: Mapped[dict] = mapped_column(JSON, nullable=True)  # TODO: 生データのマスク処理を追加する
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_login: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), server_onupdate=func.now())
