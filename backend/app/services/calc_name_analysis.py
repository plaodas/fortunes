from app import models
from app.services.constants import FORTUNE_POINT, KAKUSUU_FORTUNE, TOUGEN_FORTUNE
from sqlalchemy.orm import Session


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


def get_gogaku(sei: list[tuple[str, int]], mei: list[tuple[str, int]]) -> dict[str, int]:
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

    def get_gogaku_dict(value: int) -> dict:
        """Get the fortune dictionary for a given stroke count value."""
        return {
            "値": value,
            "吉凶": KAKUSUU_FORTUNE.get(value),
            "吉凶ポイント": FORTUNE_POINT.get(KAKUSUU_FORTUNE.get(value)),
            "桃源": {
                "短文": TOUGEN_FORTUNE.get(KAKUSUU_FORTUNE.get(value)).get("短文") if KAKUSUU_FORTUNE.get(value) else "",
                "長文": TOUGEN_FORTUNE.get(KAKUSUU_FORTUNE.get(value)).get("長文") if KAKUSUU_FORTUNE.get(value) else "",
            },
        }

    # Build a dictionary of character to stroke count
    kakusuu_dict = {}
    for ch in sei + mei:
        if ch is None:
            continue
        char, strokes = ch
        kakusuu_dict[char] = strokes

    # 画数
    sei_kakusu = sum_kakusuu(sei)
    mei_kakusu = sum_kakusuu(mei)

    # 五格
    tenkaku = sei_kakusu  # 姓の画数合計
    jinkaku = sum_kakusuu([sei[-1], mei[0]]) if sei and mei else 0  # 姓の最後の字と名の最初の字の画数合計
    chikaku = mei_kakusu  # 名の画数合計
    soukaku = sei_kakusu + mei_kakusu  # 姓名すべての画数合計
    gaikaku = soukaku - jinkaku  # 総格 − 人格

    return {"五格": {"天格": get_gogaku_dict(tenkaku), "人格": get_gogaku_dict(jinkaku), "地格": get_gogaku_dict(chikaku), "外格": get_gogaku_dict(gaikaku), "総格": get_gogaku_dict(soukaku)}}


"""
- 天格：苗字の総画数。家系や先祖からの影響。吉凶関係なし
- 人格：姓の最後の字＋名の最初の字の画数。性格や才能の中心。
- 地格：名前の総画数。若年期の運勢や基盤。
- 外格：総画数－人格。人間関係や外部からの評価。
- 総格：姓名全体の画数。晩年や人生全体の運勢。
"""
