CREATE TABLE IF NOT EXISTS analyses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    birth_datetime TIMESTAMPTZ NOT NULL,
    birth_tz TEXT NOT NULL DEFAULT 'Asia/Tokyo',
    result_birth JSONB NOT NULL,
    result_name JSONB NOT NULL,
    summary TEXT,
    detail TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
COMMENT ON COLUMN analyses.name IS '姓名';
COMMENT ON COLUMN analyses.birth_datetime IS 'UTCで保存';
COMMENT ON COLUMN analyses.birth_tz IS 'IANA timezone string';
COMMENT ON COLUMN analyses.result_birth IS '四柱推命の結果';
COMMENT ON COLUMN analyses.result_name IS '姓名判断の結果';
COMMENT ON COLUMN analyses.summary IS '短い鑑定文';
COMMENT ON COLUMN analyses.detail IS '詳細な鑑定文';


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
COMMENT ON COLUMN kanji.char IS '漢字一文字';
COMMENT ON COLUMN kanji.codepoint IS 'Unicode codepoint (e.g., U+4E00)';
COMMENT ON COLUMN kanji.strokes_text IS '元データの画数表記';
COMMENT ON COLUMN kanji.strokes_min IS '最小画数';
COMMENT ON COLUMN kanji.strokes_max IS '最大画数';
COMMENT ON COLUMN kanji.source IS 'データソース情報';

CREATE TABLE IF NOT EXISTS llm_responses (
    id SERIAL PRIMARY KEY,
    request_id TEXT,
    provider TEXT,
    model TEXT,
    model_version TEXT,
    response_id TEXT,
    prompt_hash TEXT,
    response_text TEXT,
    usage JSONB,
    raw JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON COLUMN llm_responses.request_id IS 'LLM request identifier for relation with user request';
COMMENT ON COLUMN llm_responses.provider IS 'LLM provider name for price analyze. example ''openai'', ''azure'', ''anthropic''';
COMMENT ON COLUMN llm_responses.model IS 'Model name e.g. ''gpt-4o'', ''claude-2''';
COMMENT ON COLUMN llm_responses.model_version IS 'Model version for price analyze, e.g. ''2024-06-13'', ''2024-05-23''';
COMMENT ON COLUMN llm_responses.response_id IS 'LLM response identifier';
COMMENT ON COLUMN llm_responses.prompt_hash IS 'Hash of the prompt for deduplication';
COMMENT ON COLUMN llm_responses.response_text IS 'Textual response from the LLM';
COMMENT ON COLUMN llm_responses.usage IS 'Token usage statistics';
COMMENT ON COLUMN llm_responses.raw IS 'Raw JSON response from the LLM provider';
