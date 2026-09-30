from import_kangxi import kangxi_strokes, parse_line


def test_kangxi_stroke_count_adds_radical_strokes():
    # 道 = 康熙部首 162（辵・7画）+ 残画 9
    assert kangxi_strokes("162.9") == 16
    assert kangxi_strokes("1.0") == 1
    parsed = parse_line("U+9053\t16")
    assert parsed is not None
    assert parsed[0] == "道"
    assert parsed[2] == 16
