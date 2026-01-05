INSERT INTO public.kanji (char, codepoint, strokes_text, strokes_min, strokes_max, source) VALUES
('太', 'U+592A', 4, 4, 4, 'ucs-strokes.txt,v'),
('郎', 'U+90CE', 9, 9, 9, 'ucs-strokes.txt,v')
ON CONFLICT (char) DO NOTHING;
