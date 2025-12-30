"""Import kanji stroke counts from `ucs-strokes.txt,v` into the `kanji` table.

Usage:
  PYTHONPATH=./backend python backend/import_kanji.py

This script looks for the file at `backend/app/migrations/ucs-strokes.txt,v` (or
`backend/app/migrations/ucs-strokes.txt`) and imports entries of the form
`U+4E00\t1` or `U+4E3D\t7,8` into Postgres using the app `db.engine`.
"""

import os
import re

from app import db
from sqlalchemy import text

DEFAULT_PATHS = [
    os.path.join(os.path.dirname(__file__), "migrations", "ucs-strokes.txt,v"),
    os.path.join(os.path.dirname(__file__), "migrations", "ucs-strokes.txt"),
]


def find_file():
    for p in DEFAULT_PATHS:
        if os.path.exists(p):
            return p
    return None


def parse_line(line: str):
    # match lines like: U+4E00\t1  or U+4E3D\t7,8
    m = re.match(r"^U\+([0-9A-Fa-f]+)\s+(\S+)", line)
    if not m:
        return None
    hexcp = m.group(1)
    strokes_text = m.group(2)
    try:
        cp = int(hexcp, 16)
        char = chr(cp)
    except Exception:
        return None

    # parse min/max if comma separated
    parts = strokes_text.split(",")
    try:
        nums = [int(p) for p in parts if p.isdigit()]
    except Exception:
        nums = []

    strokes_min = min(nums) if nums else None
    strokes_max = max(nums) if nums else None

    return {
        "char": char,
        "codepoint": f"U+{hexcp}",
        "strokes_text": strokes_text,
        "strokes_min": strokes_min,
        "strokes_max": strokes_max,
    }


def import_file(path: str, source_label: str | None = None) -> None:
    print(f"Importing from {path}...")
    inserted = 0
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = parse_line(line)
            if not rec:
                continue
            # insert/update
            with db.engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO kanji (char, codepoint, strokes_text, strokes_min, strokes_max, source)
                        VALUES (:char, :codepoint, :strokes_text, :strokes_min, :strokes_max, :source)
                        ON CONFLICT (char) DO UPDATE
                          SET codepoint = EXCLUDED.codepoint,
                              strokes_text = EXCLUDED.strokes_text,
                              strokes_min = EXCLUDED.strokes_min,
                              strokes_max = EXCLUDED.strokes_max,
                              source = EXCLUDED.source
                        """
                    ),
                    {
                        "char": rec["char"],
                        "codepoint": rec["codepoint"],
                        "strokes_text": rec["strokes_text"],
                        "strokes_min": rec["strokes_min"],
                        "strokes_max": rec["strokes_max"],
                        "source": source_label,
                    },
                )
            inserted += 1
            if inserted % 1000 == 0:
                print(f"Imported {inserted} rows...")

    print(f"Done. Inserted/updated {inserted} rows.")


if __name__ == "__main__":
    path = find_file()
    if not path:
        print("Could not find ucs-strokes file in expected locations:")
        for p in DEFAULT_PATHS:
            print("  ", p)
        raise SystemExit(1)
    import_file(path, source_label=os.path.basename(path))
