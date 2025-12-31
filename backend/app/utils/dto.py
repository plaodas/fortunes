# utils/dto.py
from typing import Iterable, List, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def dto_list(items: Iterable[object], dto: Type[T]) -> List[T]:
    return [dto.model_validate(item, from_attributes=True) for item in items]


def dto_one(item: object, dto: Type[T]) -> T:
    return dto.model_validate(item, from_attributes=True)
