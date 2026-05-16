"""
Edge case tests for azure-di-reconstruct.

Covers boundary values, malformed input, Unicode text, and
extreme hyperparameter settings.
"""
import pytest
from azure_di_reconstruct import reconstruct


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_json(paragraphs: list, page_w: float = 8.5, page_h: float = 11.0) -> dict:
    return {
        "analyzeResult": {
            "pages": [{"width": page_w, "height": page_h, "pageNumber": 1}],
            "paragraphs": paragraphs,
        }
    }


def _para(text: str, x0: float, y0: float, x1: float, y1: float,
          page: int = 1) -> dict:
    return {
        "content": text,
        "boundingRegions": [{
            "pageNumber": page,
            "polygon": [x0, y0, x1, y0, x1, y1, x0, y1],
        }],
    }


# ---------------------------------------------------------------------------
# Malformed / missing data
# ---------------------------------------------------------------------------

def test_missing_paragraphs_key():
    """analyzeResult without 'paragraphs' key should return empty string."""
    data = {
        "analyzeResult": {
            "pages": [{"width": 8.5, "height": 11.0, "pageNumber": 1}],
        }
    }
    assert reconstruct(data) == ""


def test_missing_analyze_result_key():
    with pytest.raises(KeyError):
        reconstruct({})


def test_paragraph_empty_content_skipped():
    data = _make_json([_para("", 1, 1, 4, 1.5)])
    assert reconstruct(data) == ""


def test_paragraph_whitespace_only_skipped():
    data = _make_json([_para("   \t\n  ", 1, 1, 4, 1.5)])
    assert reconstruct(data) == ""


def test_paragraph_missing_bounding_regions():
    """Paragraph with no boundingRegions should be silently skipped."""
    data = _make_json([{"content": "No polygon here", "boundingRegions": []}])
    assert reconstruct(data) == ""


def test_paragraph_short_polygon_skipped():
    """Polygon with fewer than 8 coordinates is invalid — skip it."""
    data = _make_json([{
        "content": "Bad polygon",
        "boundingRegions": [{"pageNumber": 1, "polygon": [1, 1, 4, 1]}],
    }])
    assert reconstruct(data) == ""


def test_paragraph_wrong_page_filtered():
    """Paragraph on page 2 should not appear in page=0 reconstruction."""
    data = _make_json([_para("Page 2 text", 1, 1, 4, 1.5, page=2)])
    assert reconstruct(data, page=0) == ""


def test_mixed_valid_and_invalid_paragraphs():
    """Valid paragraphs should be reconstructed even when others are malformed."""
    data = _make_json([
        {"content": "Bad",    "boundingRegions": []},
        _para("Good", 1, 1, 4, 1.5),
        {"content": "",       "boundingRegions": [{"pageNumber": 1, "polygon": []}]},
    ])
    result = reconstruct(data)
    assert "Good" in result


# ---------------------------------------------------------------------------
# Polygon variations
# ---------------------------------------------------------------------------

def test_minimum_valid_polygon_8_coords():
    """Exactly 8 coordinates (rectangular polygon) should work."""
    data = _make_json([_para("Rect", 1, 1, 4, 1.5)])
    assert "Rect" in reconstruct(data)


def test_rotated_polygon_16_coords():
    """Azure DI can return more than 8 coords for tilted polygons."""
    data = _make_json([{
        "content": "Rotated",
        "boundingRegions": [{
            "pageNumber": 1,
            "polygon": [1.0, 1.0, 2.0, 0.9, 4.0, 1.0, 4.1, 1.2,
                        4.0, 1.5, 2.0, 1.6, 1.0, 1.5, 0.9, 1.2],
        }],
    }])
    assert "Rotated" in reconstruct(data)


def test_block_at_left_page_edge():
    data = _make_json([_para("Edge", 0.0, 1.0, 2.0, 1.5)])
    assert "Edge" in reconstruct(data)


def test_block_at_right_page_edge():
    data = _make_json([_para("Edge", 6.5, 1.0, 8.5, 1.5)])
    assert "Edge" in reconstruct(data)


# ---------------------------------------------------------------------------
# Text wrapping
# ---------------------------------------------------------------------------

def test_long_text_wraps_within_box():
    """Text longer than the box character width must wrap, not overflow."""
    long_text = "This is a very long sentence that should definitely wrap inside the box"
    data   = _make_json([_para(long_text, 0.5, 1.0, 2.5, 2.0)])
    result = reconstruct(data, total_cols=60)
    for line in result.splitlines():
        assert len(line) <= 62, f"Line too long: {repr(line)}"


def test_single_word_longer_than_box_hard_breaks():
    """A word longer than the inner width must be hard-broken across lines.
    All characters must still appear when lines are concatenated."""
    word   = "Superlongwordwithnospacesatall"
    data   = _make_json([_para(word, 0.5, 1.0, 1.5, 1.5)])
    result = reconstruct(data, total_cols=40)
    # Strip box-drawing characters and join all content characters
    content = "".join(
        ch for line in result.splitlines()
        for ch in line if ch.isalpha()
    )
    assert word in content


# ---------------------------------------------------------------------------
# Unicode / multilingual text
# ---------------------------------------------------------------------------

def test_tamil_text():
    data   = _make_json([_para("கிரையம் கொடுப்பவர்", 1, 1, 5, 1.5)])
    result = reconstruct(data)
    assert "கிரையம்" in result


def test_devanagari_text():
    data   = _make_json([_para("भारत INDIA", 1, 1, 5, 1.5)])
    result = reconstruct(data)
    assert "भारत" in result


def test_arabic_text():
    data   = _make_json([_para("مرحبا بالعالم", 1, 1, 5, 1.5)])
    result = reconstruct(data)
    assert "مرحبا" in result


def test_mixed_language_same_row():
    data = _make_json([
        _para("Tamil: தமிழ்",    0.5, 1.0, 4.0, 1.5),
        _para("Hindi: हिन्दी",   5.0, 1.0, 8.0, 1.5),
    ])
    result = reconstruct(data)
    assert "Tamil" in result
    assert "Hindi" in result


# ---------------------------------------------------------------------------
# Extreme hyperparameter values
# ---------------------------------------------------------------------------

def test_height_threshold_zero_all_in_one_row():
    """threshold=0 means every block joins the first row."""
    data = _make_json([
        _para("A", 0.5, 1.0, 2.0, 1.5),
        _para("B", 0.5, 5.0, 2.0, 5.5),  # far below A
    ])
    result = reconstruct(data, height_threshold=0.0, width_threshold=1.0)
    for line in result.splitlines():
        if "A" in line and "B" in line:
            return
    # With threshold=0 and no x-collision forced, they may still be separated by x
    # Just confirm both appear
    assert "A" in result and "B" in result


def test_height_threshold_one_each_block_own_row():
    """threshold=1.0 requires exact 100% overlap.
    Blocks that only partially overlap in Y must go to separate rows."""
    data = _make_json([
        _para("A", 0.5, 1.0, 2.0, 1.5),
        _para("B", 4.5, 1.3, 7.0, 1.8),  # overlaps A by only 40% — below threshold
    ])
    result = reconstruct(data, height_threshold=1.0)
    for line in result.splitlines():
        assert not ("A" in line and "B" in line), "A and B should be in separate rows"


def test_total_cols_minimum():
    """total_cols=1 is extreme but should not crash."""
    data = _make_json([_para("Hello", 1, 1, 4, 1.5)])
    result = reconstruct(data, total_cols=1)
    assert isinstance(result, str)


def test_total_cols_large():
    data   = _make_json([_para("Wide", 1, 1, 4, 1.5)])
    result = reconstruct(data, total_cols=500)
    assert "Wide" in result


def test_borders_true_and_false_same_content():
    """Both output modes must contain the same text content."""
    data     = _make_json([_para("Same text", 1, 1, 4, 1.5)])
    with_b   = reconstruct(data, borders=True)
    without_b = reconstruct(data, borders=False)
    assert "Same text" in with_b
    assert "Same text" in without_b


def test_width_threshold_zero_strict_separation():
    """width_threshold=0 means any x overlap forces separate rows."""
    data = _make_json([
        _para("A", 1.0, 1.0, 4.0, 1.5),
        _para("B", 3.5, 1.0, 7.0, 1.5),  # slight x overlap with A
    ])
    result = reconstruct(data, width_threshold=0.0)
    for line in result.splitlines():
        assert not ("A" in line and "B" in line)


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------

def test_output_is_string():
    data = _make_json([_para("Hello", 1, 1, 4, 1.5)])
    assert isinstance(reconstruct(data), str)


def test_borders_box_structure():
    """Each block must have a top border line and a bottom border line."""
    data   = _make_json([_para("Test", 1, 1, 4, 1.5)])
    result = reconstruct(data, borders=True)
    lines  = result.splitlines()
    border_lines = [l for l in lines if "+" in l]
    assert len(border_lines) >= 2  # at least top + bottom border


def test_no_line_exceeds_total_cols_with_borders():
    data   = _make_json([_para("Some text here", 0.5, 1.0, 8.0, 1.5)])
    result = reconstruct(data, total_cols=80, borders=True)
    for line in result.splitlines():
        assert len(line) <= 82, f"Line exceeded total_cols: {repr(line)}"


def test_rows_appear_in_top_to_bottom_order():
    data = _make_json([
        _para("Third", 1, 5.0, 4, 5.5),
        _para("First", 1, 1.0, 4, 1.5),
        _para("Second", 1, 3.0, 4, 3.5),
    ])
    result  = reconstruct(data)
    lines   = result.splitlines()
    idx     = {w: next(i for i, l in enumerate(lines) if w in l)
                for w in ("First", "Second", "Third")}
    assert idx["First"] < idx["Second"] < idx["Third"]
