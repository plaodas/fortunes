from datetime import date

import pytest
from app import models
from app.api.v1.endpoints.analyze_enqueue import validate_kanji_characters
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
        AnalyzeRequest(name_sei="", name_mei="太郎", birth_date="1990-01-15", birth_hour=5)


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


# kanjiテーブルの文字存在確認ロジックのテスト
def test_validate_kanji_characters():
    class FakeAsyncSession:
        def __init__(self, existing_chars):
            self.existing_chars = existing_chars

        """ Simulate the execute method of an AsyncSession
        stmt = select(models.Kanji).where(models.Kanji.char.in_(chars))
        kanji = await db_session.execute(stmt)
        """

        async def execute(self, stmt):
            class FakeResult:
                def __init__(self, chars):
                    self.chars = chars

                def fetchall(self):
                    return [(models.Kanji(char=c),) for c in self.chars]

            # Extract the characters being queried from the statement
            queried_chars = stmt._whereclause.right.value
            found_chars = [c for c in queried_chars if c in self.existing_chars]
            return FakeResult(found_chars)

    fake_db_session = FakeAsyncSession(existing_chars={"山", "田", "太", "郎"})

    import asyncio

    async def run_tests():
        assert await validate_kanji_characters("山田", "太郎", fake_db_session) is True
        assert await validate_kanji_characters("山X", "太郎", fake_db_session) is False
        assert await validate_kanji_characters("山田", "たろう", fake_db_session) is False

    asyncio.run(run_tests())
