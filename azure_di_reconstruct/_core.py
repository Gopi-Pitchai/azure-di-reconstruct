"""
Core layout reconstruction logic.

All coordinates are in the native Azure DI unit (inches).
No external dependencies — pure Python.
"""
from __future__ import annotations


def get_bbox(poly: list[float]) -> tuple[float, float, float, float]:
    """Return axis-aligned bounding box (x0, y0, x1, y1) from a flat polygon list."""
    xs = poly[0::2]
    ys = poly[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def _y_overlap_ratio(b1: tuple, b2: tuple) -> float:
    """Y-range overlap relative to the shorter of the two segments."""
    overlap = max(0.0, min(b1[3], b2[3]) - max(b1[1], b2[1]))
    shorter = min(b1[3] - b1[1], b2[3] - b2[1])
    return overlap / shorter if shorter > 0 else 0.0


def _x_overlap_ratio(b1: tuple, b2: tuple) -> float:
    """X-range overlap relative to the shorter of the two segments."""
    overlap = max(0.0, min(b1[2], b2[2]) - max(b1[0], b2[0]))
    shorter = min(b1[2] - b1[0], b2[2] - b2[0])
    return overlap / shorter if shorter > 0 else 0.0


def group_into_rows(
    blocks: list[dict],
    height_threshold: float = 0.8,
    width_threshold: float = 0.3,
) -> list[list[dict]]:
    """
    Group blocks into rows using spatial overlap rules.

    A block joins an existing row when:
      - Its Y-range overlaps the row's Y-span by >= ``height_threshold``.
      - Its X-range does NOT overlap any block already in that row
        by >= ``width_threshold`` (prevents merging stacked blocks).

    Blocks within each row are sorted left-to-right.

    Parameters
    ----------
    blocks:
        List of block dicts, each with a ``bbox`` key (x0, y0, x1, y1).
    height_threshold:
        Minimum Y-overlap ratio to assign a block to an existing row.
    width_threshold:
        Maximum X-overlap ratio before two blocks are considered to collide.

    Returns
    -------
    list[list[dict]]
        Rows of blocks sorted top-to-bottom; within each row, left-to-right.
    """
    sorted_blocks = sorted(blocks, key=lambda b: b["bbox"][1])
    rows: list[list[dict]] = []

    for block in sorted_blocks:
        placed = False
        for row in rows:
            row_y0 = min(b["bbox"][1] for b in row)
            row_y1 = max(b["bbox"][3] for b in row)
            row_span = (0.0, row_y0, 0.0, row_y1)

            if _y_overlap_ratio(row_span, block["bbox"]) >= height_threshold:
                no_collision = all(
                    _x_overlap_ratio(block["bbox"], b["bbox"]) < width_threshold
                    for b in row
                )
                if no_collision:
                    row.append(block)
                    placed = True
                    break

        if not placed:
            rows.append([block])

    for row in rows:
        row.sort(key=lambda b: b["bbox"][0])

    return rows


def _char_wrap(text: str, max_chars: int) -> list[str]:
    """Word-wrap text to ``max_chars`` per line; hard-breaks words longer than the limit."""
    if max_chars <= 0:
        return [text]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        lines.append(current)
    return lines or [text]


def reconstruct_as_text(
    rows: list[list[dict]],
    page_w_inches: float,
    total_cols: int = 120,
    borders: bool = True,
) -> str:
    """
    Render grouped rows as a monospace text grid.

    Horizontal positions are mapped from inch coordinates to character columns
    proportionally: ``col = int(x_inches / page_w_inches * total_cols)``.

    Parameters
    ----------
    rows:
        Output of :func:`group_into_rows`.
    page_w_inches:
        Page width in inches from the Azure DI JSON.
    total_cols:
        Width of the output grid in characters.
    borders:
        If ``True`` each block is wrapped in ``+---+`` / ``| |`` box characters.
        If ``False`` text is placed spatially using spaces only.

    Returns
    -------
    str
        Monospace text grid, ready for ``print()`` or ``st.code()``.
    """
    output: list[str] = []

    for row in rows:
        row_data: list[tuple] = []
        for block in row:
            x0, _, x1, _ = block["bbox"]
            col_start = max(0, int(x0 / page_w_inches * total_cols))
            col_end   = min(total_cols - 1, int(x1 / page_w_inches * total_cols))
            inner_w   = max(1, col_end - col_start - (2 if borders else 0))
            lines     = _char_wrap(block["text"], inner_w)
            row_data.append((col_start, col_end, inner_w, lines))

        if not row_data:
            continue

        max_lines = max(len(rd[3]) for rd in row_data)

        if borders:
            top = [" "] * total_cols
            for col_start, col_end, _, _ in row_data:
                top[col_start] = "+"
                for c in range(col_start + 1, col_end):
                    top[c] = "-"
                if col_end < total_cols:
                    top[col_end] = "+"
            output.append("".join(top).rstrip())

        for li in range(max_lines):
            grid = [" "] * total_cols
            for col_start, col_end, inner_w, lines in row_data:
                text_line = lines[li] if li < len(lines) else ""
                padded    = text_line.ljust(inner_w)[:inner_w]
                if borders:
                    grid[col_start] = "|"
                    if col_end < total_cols:
                        grid[col_end] = "|"
                    offset = col_start + 1
                else:
                    offset = col_start
                for i, ch in enumerate(padded):
                    pos = offset + i
                    if pos < total_cols:
                        grid[pos] = ch
            output.append("".join(grid).rstrip())

        if borders:
            bot = [" "] * total_cols
            for col_start, col_end, _, _ in row_data:
                bot[col_start] = "+"
                for c in range(col_start + 1, col_end):
                    bot[c] = "-"
                if col_end < total_cols:
                    bot[col_end] = "+"
            output.append("".join(bot).rstrip())

        output.append("")

    return "\n".join(output)
