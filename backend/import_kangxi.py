"""康熙画数を kanji.strokes_kangxi に入れる。

データは Unicode Unihan の kRSUnicode（康熙部首番号と残画）に、
康熙部首そのものの画数を足して作る。たとえば「道」は部首 162（辵・7画）+ 残画 9 = 16画。

再生成:
  python backend/import_kangxi.py --from-unihan /path/to/Unihan_IRGSources.txt

取り込み:
  PYTHONPATH=./backend python backend/import_kangxi.py
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re

from app import db
from sqlalchemy import text

# 康熙部首 1..214 の画数
RADICAL_STROKES = [
    1, 1, 1, 1, 1, 1,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
    4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4,
    5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5,
    6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6,
    7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7,
    8, 8, 8, 8, 8, 8, 8, 8, 8, 8,
    9, 9, 9, 9, 9, 9, 9, 9, 9, 9,
    10, 10, 10, 10, 10, 10, 10, 10,
    11, 11, 11, 11, 11, 11,
    12, 12, 12, 12,
    13, 13, 13, 13,
    14, 14,
    15,
    16, 16,
    17,
]

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "migrations", "kangxi-strokes.txt")
_LINE = re.compile(r"^U\+([0-9A-Fa-f]+)\t(\d+)\s*$")


def kangxi_strokes(radical_field: str) -> int | None:
    """kRSKangXi の先頭値（例: 120'.4）から画数を返す。"""
    first = radical_field.split()[0]
    radical_text, _, extra_text = first.partition(".")
    radical_text = radical_text.replace("'", "")
    if not radical_text.isdigit() or not extra_text.isdigit():
        return None
    radical = int(radical_text)
    if radical < 1 or radical > len(RADICAL_STROKES):
        return None
    return RADICAL_STROKES[radical - 1] + int(extra_text)


def build_from_unihan(unihan_path: str, out_path: str) -> int:
    if len(RADICAL_STROKES) != 214:
        raise RuntimeError("康熙部首の画数表が 214 件ではありません")
    written = 0
    with open(unihan_path, encoding="utf-8") as src, open(out_path, "w", encoding="utf-8") as out:
        out.write("# Kangxi stroke counts: Unihan kRSUnicode radical number + Kangxi radical strokes\n")
        out.write("# https://www.unicode.org/Public/UCD/latest/ucd/Unihan.zip (Unihan_IRGSources.txt)\n")
        for line in src:
            if not line.startswith("U+"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3 or parts[1] not in ("kRSKangXi", "kRSUnicode"):
                continue
            strokes = kangxi_strokes(parts[2])
            if strokes is None:
                continue
            out.write(f"{parts[0]}\t{strokes}\n")
            written += 1
    return written


def parse_line(line: str) -> tuple[str, str, int] | None:
    matched = _LINE.match(line.strip())
    if not matched:
        return None
    hexcp = matched.group(1)
    try:
        char = chr(int(hexcp, 16))
    except ValueError:
        return None
    return char, f"U+{hexcp.upper()}", int(matched.group(2))


async def import_file(path: str) -> None:
    async with db.engine.begin() as conn:
        await conn.execute(text("ALTER TABLE kanji ADD COLUMN IF NOT EXISTS strokes_kangxi INTEGER"))
    updated = 0
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            rec = parse_line(line)
            if rec is None:
                continue
            char, codepoint, strokes = rec
            async with db.engine.begin() as conn:
                await conn.execute(
                    text(
                        """
                        INSERT INTO kanji (char, codepoint, strokes_kangxi, source)
                        VALUES (:char, :codepoint, :strokes, :source)
                        ON CONFLICT (char) DO UPDATE
                          SET strokes_kangxi = EXCLUDED.strokes_kangxi
                        """
                    ),
                    {"char": char, "codepoint": codepoint, "strokes": strokes, "source": "unihan-kRSKangXi"},
                )
            updated += 1
            if updated % 2000 == 0:
                print(f"Updated {updated} rows...")
    print(f"Done. Updated {updated} rows.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-unihan", dest="unihan", help="Unihan_RadicalStrokeCounts.txt から kangxi-strokes.txt を作る")
    parser.add_argument("--out", default=DEFAULT_PATH)
    args = parser.parse_args()
    if args.unihan:
        count = build_from_unihan(args.unihan, args.out)
        print(f"Wrote {count} rows to {args.out}")
        return
    if not os.path.exists(DEFAULT_PATH):
        raise SystemExit(f"康熙画数ファイルがありません: {DEFAULT_PATH}")
    asyncio.run(import_file(DEFAULT_PATH))


if __name__ == "__main__":
    main()
