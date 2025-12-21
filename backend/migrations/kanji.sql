-- Create kanji table for stroke counts (imported from ucs-strokes)
CREATE TABLE IF NOT EXISTS kanji (
    char TEXT PRIMARY KEY,
    codepoint TEXT NOT NULL,
    strokes_text TEXT,
    strokes_min INTEGER,
    strokes_max INTEGER,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_kanji_codepoint ON kanji(codepoint);
