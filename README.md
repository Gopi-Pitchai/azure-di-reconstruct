# azure-di-reconstruct

[![PyPI version](https://img.shields.io/pypi/v/azure-di-reconstruct)](https://pypi.org/project/azure-di-reconstruct/)
[![Python](https://img.shields.io/pypi/pyversions/azure-di-reconstruct)](https://pypi.org/project/azure-di-reconstruct/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)](https://pypi.org/project/azure-di-reconstruct/)

**Reconstruct Azure Document Intelligence JSON output into readable spatial text layouts.**

`azure-di-reconstruct` takes the JSON returned by the [Azure Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/) `prebuilt-read` (OCR/Read)
 model and reproduces the original document's two-dimensional layout as a monospace text grid -- no image file, no external dependencies.

---

## Features

- **Zero runtime dependencies** -- pure Python 3.10+
- **Language agnostic** -- works with any language Azure DI supports (Tamil, Hindi, English, Arabic, Chinese, etc.)
- **Multi-page support** -- reconstruct any page by index
- **Two output modes** -- pipe-bordered boxes or plain spatial text
- **Tunable layout** -- four hyperparameters control grouping and grid resolution
- **Lightweight** -- single function call, no setup required

---

## How It Works

Azure DI returns paragraph polygons in inch coordinates. `azure-di-reconstruct`:

1. **Extracts** paragraph bounding boxes from the JSON
2. **Groups** blocks into rows using configurable height and width overlap thresholds
3. **Maps** inch coordinates to character columns proportionally
4. **Renders** a monospace grid with each paragraph in its original spatial position

```text
+------------------------------+          +---------------------+
| ACME Corporation             |          | Invoice No: 0042    |
| 123 Business Avenue          |          | Date: 01-Jan-2025   |
+------------------------------+          +---------------------+

+----------------------------------------------------------+
| Bill To: Sample Client Ltd, 456 Client Road              |
+----------------------------------------------------------+

+------------------------------+     +--------+  +----------+
| Description                  |     | Qty    |  | Amount   |
+------------------------------+     +--------+  +----------+

+------------------------------+     +--------+  +----------+
| Software License             |     | 1      |  | $1200.00 |
+------------------------------+     +--------+  +----------+

+------------------------------+     +--------+  +----------+
| Support Package (12 months)  |     | 12     |  | $240.00  |
+------------------------------+     +--------+  +----------+

+----------------------------------------------------------+
| Subtotal: $1,440.00                                      |
+----------------------------------------------------------+

+----------------------------------------------------------+
| Tax (10%): $144.00                                       |
+----------------------------------------------------------+

+------------------------------+          +---------------------+
| Total Due: $1,584.00         |          | Due: 30-Jan-2025    |
+------------------------------+          +---------------------+
```

---

## Installation

```bash
pip install azure-di-reconstruct
```

---

## Quick Start

```python
import json
from azure_di_reconstruct import reconstruct

with open("document.json", encoding="utf-8") as f:
    data = json.load(f)

# Pipe-bordered layout (default)
print(reconstruct(data))

# Plain spatial text
print(reconstruct(data, borders=False))

# Second page, wider grid
print(reconstruct(data, page=1, total_cols=160))
```

---

## API Reference

### `reconstruct(json_data, page, height_threshold, width_threshold, total_cols, borders)`

> All parameters after `json_data` are keyword-only -- they must be passed by name:
> `reconstruct(data, page=1, borders=False)` not `reconstruct(data, 1, False)`.

| Parameter          | Type    | Default  | Description                                              |
|--------------------|---------|----------|----------------------------------------------------------|
| `json_data`        | `dict`  | required | Parsed Azure DI JSON with `analyzeResult` key            |
| `page`             | `int`   | `0`      | Zero-based page index to reconstruct                     |
| `height_threshold` | `float` | `0.8`    | Minimum Y-overlap ratio for blocks to share a row        |
| `width_threshold`  | `float` | `0.3`    | Maximum X-overlap ratio before blocks are separated      |
| `total_cols`       | `int`   | `120`    | Output grid width in characters                          |
| `borders`          | `bool`  | `True`   | Wrap blocks in box characters (`+---+` and pipe borders) |

**Returns** `str` -- monospace text grid.

**Raises** `ValueError` if `page` index exceeds the document page count.

---

## Parameter Guide

### `height_threshold`

Range: `0.0 – 1.0`. Controls whether two blocks are on the **same row or separate rows**.

- **Higher (e.g. 0.9)** -- stricter; blocks must nearly perfectly align vertically to share a row. Best for clean printed documents.
- **Lower (e.g. 0.5)** -- looser; allows blocks with rough vertical alignment to share a row. Best for handwritten or skewed scans.

### `width_threshold`

Range: `0.0 – 1.0`. Controls column separation within a row.

- **Lower (e.g. 0.1)** -- even small X overlaps force blocks into separate rows (strict column separation).
- **Higher (e.g. 0.6)** -- blocks need heavy X overlap before being separated (permissive).

### `total_cols`

Maps the page width to a fixed number of character columns.

- **Fewer columns (60-80)** -- more compressed, fits narrow terminals.
- **More columns (140-200)** -- more spatial detail, better column separation.

### `borders`

- `True` -- box characters around each block (default, best for verification)
- `False` -- plain text with spatial positioning only (best for copy-paste)

---

## Examples

### Multi-page document

```python
pages = data["analyzeResult"]["pages"]

for i in range(len(pages)):
    print(f"\n{'='*60}")
    print(f"  Page {i + 1}")
    print('='*60)
    print(reconstruct(data, page=i))
```

### Save reconstruction to file

```python
with open("reconstruction.txt", "w", encoding="utf-8") as f:
    f.write(reconstruct(data, borders=False, total_cols=120))
```

### Compare pages

```python
page_1 = reconstruct(data, page=0, total_cols=100)
page_2 = reconstruct(data, page=1, total_cols=100)
```

---

## Input Format

`azure-di-reconstruct` expects the standard Azure DI REST API response structure:

```json
{
  "analyzeResult": {
    "pages": [
      { "width": 8.5, "height": 11.0, "pageNumber": 1 }
    ],
    "paragraphs": [
      {
        "content": "Sample text",
        "boundingRegions": [
          {
            "pageNumber": 1,
            "polygon": [1.0, 1.0, 4.0, 1.0, 4.0, 1.5, 1.0, 1.5]
          }
        ]
      }
    ]
  }
}
```

If using the Azure Python SDK, wrap the result before passing to `reconstruct()`:

```python
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

result = client.begin_analyze_document("prebuilt-read", body=request).result()
data   = {"analyzeResult": result.as_dict()}
print(reconstruct(data))
```

---

## Supported Models

| Azure DI Model        | Supported    |
|-----------------------|--------------|
| `prebuilt-read` (OCR) | Full support |

> This package is designed specifically for the `prebuilt-read` (OCR/Read) output.
> Other Azure DI models are not supported.

---

## Limitations

- **Character alignment** -- non-English characters may not be monospace-width in all terminals, which can affect column alignment in the text grid.
- **Rotated pages** -- heavily rotated page scans may require pre-processing before Azure DI analysis.
- **Complex tables** -- table cells are treated as individual paragraphs; explicit table structure is not preserved.

---

## License

MIT (c) 2026 Gopi Pitchai. See [LICENSE](LICENSE) for details.
