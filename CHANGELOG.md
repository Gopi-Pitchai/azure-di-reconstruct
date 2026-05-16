# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] - 2026-05-16

### Fixed
- README: fixed all Unicode encoding corruption (em dashes, copyright symbol)
- README: replaced real personal/legal test data in example with generic invoice layout
- README: corrected supported models -- OCR/Read only
- README: updated Limitations to say "non-English characters" instead of listing scripts
- README: added parameter ranges (0.0-1.0) to height_threshold and width_threshold
- README: resolved all markdown linting warnings

---

## [0.1.0] - 2026-05-16

### Added
- Initial release of `azure-di-reconstruct`
- `reconstruct()` -- single entry-point function for Azure DI `prebuilt-read` JSON
- Height-overlap and width-overlap based row grouping algorithm
- Pipe-bordered box output mode (`borders=True`)
- Plain spatial text output mode (`borders=False`)
- Multi-page document support via `page` parameter
- Four tunable hyperparameters: `height_threshold`, `width_threshold`, `total_cols`, `borders`
- Zero runtime dependencies -- pure Python 3.10+
- Full type annotations throughout
- MIT license
