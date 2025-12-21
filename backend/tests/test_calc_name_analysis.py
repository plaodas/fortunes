from app import db
from app.services.calc_name_analysis import get_kanji


def test_get_kanji() -> None:
    kanji = "山"
    with db.SessionLocal() as session:
        assert 3 == get_kanji(session, kanji)
        assert None is get_kanji(session, "😻")  # not in DB}
