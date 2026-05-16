"""
Block extraction for Azure Document Intelligence prebuilt-read (OCR) output.
"""
from __future__ import annotations

from ._core import get_bbox


def extract_blocks(data: dict, page_number: int = 1) -> list[dict]:
    """
    Extract paragraph blocks from an Azure DI ``prebuilt-read`` result.

    Parameters
    ----------
    data:
        Parsed Azure DI JSON with the ``analyzeResult`` wrapper.
    page_number:
        1-based page number to extract (matches the ``pageNumber`` field
        returned by Azure DI). Defaults to ``1`` (first page).

    Returns
    -------
    list[dict]
        Each dict contains:

        - ``text``  — paragraph text content
        - ``bbox``  — ``(x0, y0, x1, y1)`` axis-aligned bounding box in inches
    """
    blocks: list[dict] = []

    for paragraph in data["analyzeResult"].get("paragraphs", []):
        regions  = paragraph.get("boundingRegions") or []
        if not regions:
            continue
        region   = regions[0]
        if region.get("pageNumber", 1) != page_number:
            continue

        raw_poly = region.get("polygon", [])
        text     = paragraph.get("content", "").strip()

        if len(raw_poly) < 8 or not text:
            continue

        blocks.append({
            "text": text,
            "bbox": get_bbox(raw_poly),
        })

    return blocks
