from datetime import date

import pytest
from app.schemas.inputs.analyze_request import AnalyzeRequest
from pydantic import ValidationError


def test_valid_request_parses():
    req = AnalyzeRequest(name_sei="山田", name_mei="太郎", birth_date="1990-01-15", birth_hour=5)
    assert req.name_sei == "山田"
    assert req.name_mei == "太郎"
    assert req.birth_date == date(1990, 1, 15)
    assert req.birth_hour == 5


def test_name_too_short():
    with pytest.raises(ValidationError):
        AnalyzeRequest(name_sei="A", name_mei="太郎", birth_date="1990-01-15", birth_hour=5)


def test_name_too_long():
    long_name = "x" * 51
    with pytest.raises(ValidationError):
        AnalyzeRequest(name_sei=long_name, name_mei="太郎", birth_date="1990-01-15", birth_hour=5)


def test_invalid_birth_date():
    with pytest.raises(ValidationError):
        AnalyzeRequest(name_sei="山田", name_mei="太郎", birth_date="1990-02-30", birth_hour=5)


def test_birth_hour_out_of_range():
    with pytest.raises(ValidationError):
        AnalyzeRequest(name_sei="山田", name_mei="太郎", birth_date="1990-01-15", birth_hour=24)

    with pytest.raises(ValidationError):
        AnalyzeRequest(name_sei="山田", name_mei="太郎", birth_date="1990-01-15", birth_hour=-1)
