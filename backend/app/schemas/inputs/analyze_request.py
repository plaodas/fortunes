from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    name_sei: Annotated[str, Field(min_length=1, max_length=50)]
    name_mei: Annotated[str, Field(min_length=1, max_length=50)]
    birth_date: date  # parsed from "YYYY-MM-DD"
    birth_hour: Annotated[int, Field(ge=0, le=23)]
