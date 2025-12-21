from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    name: str
    birth_date: str  # YYYY-MM-DD
    birth_hour: int  # 0-23
