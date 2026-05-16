"""
Tests for azure-di-reconstruct.

Run with:  pytest tests/
"""
import pytest
from azure_di_reconstruct import reconstruct, __version__


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_json(paragraphs: list, page_w: float = 8.5, page_h: float = 11.0) -> dict:
    """Build a minimal Azure DI JSON fixture."""
    return {
        "analyzeResult": {
            "pages": [{"width": page_w, "height": page_h, "pageNumber": 1}],
            "paragraphs": paragraphs,
        }
    }


def _para(text: str, x0: float, y0: float, x1: float, y1: float,
          page: int = 1) -> dict:
    """Create a paragraph fixture with a rectangular polygon."""
    return {
        "content": text,
        "boundingRegions": [{
            "pageNumber": page,
            "polygon": [x0, y0, x1, y0, x1, y1, x0, y1],
        }],
    }


# ---------------------------------------------------------------------------
# Package metadata
# ---------------------------------------------------------------------------

def test_version_format():
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


# ---------------------------------------------------------------------------
# Basic reconstruction
# ---------------------------------------------------------------------------

def test_single_block_borders():
    data   = _make_json([_para("Hello World", 1, 1, 4, 1.5)])
    result = reconstruct(data)
    assert "Hello World" in result
    assert "+" in result
    assert "|" in result


def test_single_block_no_borders():
    data   = _make_json([_para("Hello World", 1, 1, 4, 1.5)])
    result = reconstruct(data, borders=False)
    assert "Hello World" in result
    assert "+" not in result


def test_empty_document():
    data   = _make_json([])
    result = reconstruct(data)
    assert result == ""


# ---------------------------------------------------------------------------
# Row grouping
# ---------------------------------------------------------------------------

def test_two_columns_same_row():
    """Blocks with high Y-overlap and no X-overlap should share a row."""
    data = _make_json([
        _para("Left",  0.5, 1.0, 3.5, 1.5),
        _para("Right", 5.0, 1.0, 8.0, 1.5),
    ])
    result = reconstruct(data)
    # Both texts must appear on the same text line (between the same pair of borders)
    for line in result.splitlines():
        if "Left" in line and "Right" in line:
            return
    pytest.fail("Left and Right were not placed on the same row")


def test_two_rows_stacked():
    """Blocks with no Y-overlap should be in separate rows."""
    data = _make_json([
        _para("Top",    1, 1.0, 5, 1.5),
        _para("Bottom", 1, 3.0, 5, 3.5),
    ])
    result  = reconstruct(data)
    lines   = result.splitlines()
    top_idx = next(i for i, l in enumerate(lines) if "Top"    in l)
    bot_idx = next(i for i, l in enumerate(lines) if "Bottom" in l)
    assert bot_idx > top_idx


# ---------------------------------------------------------------------------
# Multi-page
# ---------------------------------------------------------------------------

def test_page_index_zero():
    data = {
        "analyzeResult": {
            "pages": [
                {"width": 8.5, "height": 11.0, "pageNumber": 1},
                {"width": 8.5, "height": 11.0, "pageNumber": 2},
            ],
            "paragraphs": [
                _para("Page one content", 1, 1, 6, 1.5, page=1),
                _para("Page two content", 1, 1, 6, 1.5, page=2),
            ],
        }
    }
    assert "Page one content" in reconstruct(data, page=0)
    assert "Page two content" not in reconstruct(data, page=0)


def test_page_index_one():
    data = {
        "analyzeResult": {
            "pages": [
                {"width": 8.5, "height": 11.0, "pageNumber": 1},
                {"width": 8.5, "height": 11.0, "pageNumber": 2},
            ],
            "paragraphs": [
                _para("Page one content", 1, 1, 6, 1.5, page=1),
                _para("Page two content", 1, 1, 6, 1.5, page=2),
            ],
        }
    }
    assert "Page two content" in reconstruct(data, page=1)
    assert "Page one content" not in reconstruct(data, page=1)


def test_invalid_page_raises():
    data = _make_json([])
    with pytest.raises(ValueError, match="out of range"):
        reconstruct(data, page=5)


# ---------------------------------------------------------------------------
# Hyperparameters
# ---------------------------------------------------------------------------

def test_total_cols_affects_width():
    data    = _make_json([_para("Test", 1, 1, 4, 1.5)])
    narrow  = reconstruct(data, total_cols=60)
    wide    = reconstruct(data, total_cols=160)
    assert max(len(l) for l in narrow.splitlines()) < max(len(l) for l in wide.splitlines())


def test_height_threshold_grouping():
    """Lower threshold groups more blocks into the same row."""
    data = _make_json([
        _para("A", 0.5, 1.0, 3.0, 1.5),
        _para("B", 5.0, 1.2, 8.0, 1.7),   # 60% Y-overlap with A
    ])
    strict = reconstruct(data, height_threshold=0.8)
    loose  = reconstruct(data, height_threshold=0.5)

    def same_row(result):
        for line in result.splitlines():
            if "A" in line and "B" in line:
                return True
        return False

    assert not same_row(strict)
    assert same_row(loose)
