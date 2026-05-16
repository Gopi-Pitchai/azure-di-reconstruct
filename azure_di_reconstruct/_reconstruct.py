"""
Main entry point — ties extraction, grouping, and rendering together.
"""
from __future__ import annotations

from ._core import group_into_rows, reconstruct_as_text
from ._ocr import extract_blocks


def reconstruct(
    json_data: dict,
    *,
    page: int = 0,
    height_threshold: float = 0.8,
    width_threshold: float = 0.3,
    total_cols: int = 120,
    borders: bool = True,
) -> str:
    """
    Reconstruct an Azure Document Intelligence JSON result into a spatial text layout.

    Accepts the JSON returned by the ``prebuilt-read`` model (OCR).
    Coordinates are read in the native Azure DI unit (inches) — no image file required.

    Parameters
    ----------
    json_data : dict
        Parsed Azure DI JSON. Must contain the ``analyzeResult`` key as returned
        by the REST API or wrapped from the Python SDK result.
    page : int
        Zero-based page index to reconstruct. Default is ``0`` (first page).
    height_threshold : float
        Minimum Y-overlap ratio (0–1) for two blocks to be placed on the same
        row. Higher values require tighter vertical alignment. Default: ``0.8``.
    width_threshold : float
        Maximum X-overlap ratio (0–1) before two same-row blocks are forced into
        separate rows. Lower values enforce stricter column separation.
        Default: ``0.3``.
    total_cols : int
        Character width of the output grid. Higher values preserve more spatial
        detail but require wider terminals. Default: ``120``.
    borders : bool
        If ``True`` (default), wraps each text block in ``+---+`` / ``| |``
        box-drawing characters for clear visual separation.
        If ``False``, renders plain text with spatial positioning only.

    Returns
    -------
    str
        Monospace text grid representing the reconstructed document layout.
        Each paragraph polygon becomes a positioned text block.

    Raises
    ------
    KeyError
        If ``json_data`` does not contain the expected ``analyzeResult`` structure.
    ValueError
        If the requested ``page`` index exceeds the number of pages in the document.

    Examples
    --------
    >>> import json
    >>> from di_reconstruct import reconstruct
    >>>
    >>> with open("document.json", encoding="utf-8") as f:
    ...     data = json.load(f)
    >>>
    >>> print(reconstruct(data))
    >>> print(reconstruct(data, borders=False, total_cols=100))
    """
    analyze_result = json_data["analyzeResult"]
    pages          = analyze_result["pages"]

    if page >= len(pages):
        raise ValueError(
            f"Page index {page} is out of range. "
            f"The document has {len(pages)} page(s) (0-based indexing)."
        )

    page_info    = pages[page]
    page_w       = page_info["width"]
    page_number  = page + 1  # Azure DI uses 1-based page numbers

    blocks = extract_blocks(json_data, page_number=page_number)
    rows   = group_into_rows(blocks, height_threshold, width_threshold)
    return reconstruct_as_text(rows, page_w, total_cols, borders)
