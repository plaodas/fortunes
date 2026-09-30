from typing import Optional, TypedDict

from app import models
from app.services.constants import FORTUNE_POINT, KAKUSUU_FORTUNE, TOUGEN_FORTUNE
from sqlalchemy.orm import Session


class TougenDict(TypedDict):
    短文: str
    長文: str


class GogakuEntry(TypedDict):
    値: int
    吉凶: Optional[str]
    吉凶ポイント: Optional[int]
    桃源: TougenDict


class GokakuDict(TypedDict):
    五格: dict[str, GogakuEntry]


def get_kanji(session: Session, char: str) -> tuple[str, int] | None:
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
        return char, 0
    return char, int(k.strokes_min)


def _gaikaku(sei: list[tuple[str, int]], mei: list[tuple[str, int]], soukaku: int, jinkaku: int) -> int:
    """熊崎式の外格。"""
    sei_count = len(sei)
    mei_count = len(mei)
    if sei_count == 1 and mei_count == 1:
        return 2
    if sei_count == 1 and mei_count >= 2:
        return sum(strokes for _char, strokes in mei[1:]) + 1
    if sei_count >= 2 and mei_count == 1:
        return sei[0][1] + 1
    return soukaku - jinkaku


def get_gogaku(sei: list[tuple[str, int]], mei: list[tuple[str, int]]) -> GokakuDict:
    """Calculate the Five Grids (五格) based on the strokes of the surname (姓) and given name (名).
    Args:
        sei (list[tuple[str, int]]): List of stroke counts for surname characters
        mei (list[tuple[str, int]]): List of stroke counts for given name characters
    Returns:
        dict: A dictionary containing the Five Grids with their respective stroke counts
    """

    def sum_kakusuu(name_chars: list[tuple[str, int]]) -> int:
        """Sum the stroke counts for a list of characters."""
        total = 0
        for ch in name_chars:
            _, strokes = ch
            total += strokes
        return total

    def get_gogaku_dict(value: int) -> GogakuEntry:
        """Get the fortune dictionary for a given stroke count value."""
        fortune_key = KAKUSUU_FORTUNE.get(value)
        fortune_point = FORTUNE_POINT.get(fortune_key) if fortune_key is not None else None
        tougen = TOUGEN_FORTUNE.get(fortune_key) if fortune_key is not None else None
        short = tougen.get("短文") if tougen is not None else ""
        if short is None:
            short = ""
        long = tougen.get("長文") if tougen is not None else ""
        if long is None:
            long = ""

        return {
            "値": value,
            "吉凶": fortune_key,
            "吉凶ポイント": fortune_point,
            "桃源": {
                "短文": short,
                "長文": long,
            },
        }

    # Build a dictionary of character to stroke count
    kakusuu_dict = {}
    for ch in sei + mei:
        if ch is None:
            continue
        char, strokes = ch
        kakusuu_dict[char] = strokes

    # 画数（熊崎式）。天格・地格の +1 は総格には入れない。
    sei_kakusu = sum_kakusuu(sei)
    mei_kakusu = sum_kakusuu(mei)
    sei_count = len(sei)
    mei_count = len(mei)

    tenkaku = sei_kakusu + (1 if sei_count == 1 else 0)
    chikaku = mei_kakusu + (1 if mei_count == 1 else 0)
    jinkaku = sum_kakusuu([sei[-1], mei[0]]) if sei and mei else 0
    soukaku = sei_kakusu + mei_kakusu
    gaikaku = _gaikaku(sei, mei, soukaku, jinkaku)

    return {"五格": {"天格": get_gogaku_dict(tenkaku), "人格": get_gogaku_dict(jinkaku), "地格": get_gogaku_dict(chikaku), "外格": get_gogaku_dict(gaikaku), "総格": get_gogaku_dict(soukaku)}}


"""
- 天格：姓の画数。1字なら +1。
- 人格：姓の最後の字＋名の最初の字。
- 地格：名の画数。1字なら +1。
- 外格：単姓単名は 2。単姓複名は名の2字目以降 +1。複姓単名は姓の1字目 +1。複姓複名は総格 − 人格。
- 総格：姓名の実画数合計。+1 は入れない。
"""
