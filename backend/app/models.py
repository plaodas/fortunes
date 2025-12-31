from datetime import date, datetime

from sqlalchemy import JSON, TIMESTAMP, Date, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    birth_hour: Mapped[int] = mapped_column(Integer, nullable=False)
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
