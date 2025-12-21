from pydantic import BaseModel


class AnalysisOut(BaseModel):
    id: int
    name: str
    birth_date: str
    birth_hour: int
    result_birth: dict
    result_name: dict
    summary: str
    created_at: str | None = None
