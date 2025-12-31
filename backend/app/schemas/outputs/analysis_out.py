from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class AnalysisOut(BaseModel):
    id: int
    name: str
    birth_date: date  # ← date 型で受ける
    birth_hour: int
    result_name: dict
    result_birth: dict
    summary: str | None
    detail: str | None
    created_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
