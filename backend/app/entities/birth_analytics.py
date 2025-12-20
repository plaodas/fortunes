
from pydantic import BaseModel


class Meishiki(BaseModel):
    year: str
    month: str
    day: str
    hour: str
