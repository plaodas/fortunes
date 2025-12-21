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
