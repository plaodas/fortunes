from app import models
from sqlalchemy.orm import Session


def get_kanji(session: Session, char: str) -> int | None:
    """Return kanji stroke info for a single character.
    Args:
        session: SQLAlchemy Session object
        char (str): A single kanji character
    Returns:
        int | None: Stroke count if found, else None
    """
    if not char:
        return None
    # only first character
    ch = char[0]
    # Use ORM get since `char` is the primary key
    k = session.get(models.Kanji, ch)
    if not k or k.strokes_min is None:
        return None
    return int(k.strokes_min)
