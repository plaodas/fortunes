from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    name_sei: str
    name_mei: str
    birth_date: str  # YYYY-MM-DD
    birth_hour: int  # 0-23
