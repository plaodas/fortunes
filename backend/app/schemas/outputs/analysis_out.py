from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AnalysisOut(BaseModel):
    id: int
    name: str
    birth_date: date  # ← date 型で受ける
    birth_hour: int
    birth_tz: str
    result_name: dict[str, Any]
    result_birth: dict[str, Any]
    summary: str | None
    detail: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
