from sqlalchemy import JSON, TIMESTAMP, Column, Date, Integer, Text
from sqlalchemy.sql import func

from .db import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(Text, nullable=False)
    birth_date = Column(Date, nullable=False)
    birth_hour = Column(Integer, nullable=False)
    result_birth = Column(JSON, nullable=False)
    result_name = Column(JSON, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


class Kanji(Base):
    __tablename__ = "kanji"

    char = Column(Text, primary_key=True)
    codepoint = Column(Text, nullable=False)
    strokes_text = Column(Text, nullable=True)
    strokes_min = Column(Integer, nullable=True)
    strokes_max = Column(Integer, nullable=True)
    source = Column(Text, nullable=True)
