# Coding Conventions

**Analysis Date:** 2026-06-24

## Naming Patterns

**Files:**
- Script entry points use hyphens: `build-pdf.py`, `generate-panels.py`
- Constants use SCREAMING_SNAKE_CASE: `ARXIV_ID`, `CHROME_CANDIDATES`, `PANELS`, `OUT_PDF`
- Module-level paths are uppercase: `ROOT`, `ARXIV_PDF_URL`

**Functions:**
- All lowercase with underscores: `find_root()`, `find_chrome()`, `cover_and_comic_html()`, `render_front_pdf()`, `main()`
- Helper/private functions use leading underscore: `_download_curl()` in `build/build-pdf.py`
- Descriptive names that indicate purpose: `extract_prompt()`, `page_files()`, `image_url_from_result()`

**Variables:**
- lowercase snake_case throughout: `chrome`, `work`, `md_path`, `out_dir`, `pages_dir`
- Descriptive names preferred over abbreviations: `chrome_profile` instead of `cp`, `html_path` instead of `hp`

**Types:**
- Type hints using `from __future__ import annotations` (Python 3.10+)
- Union types use `|` syntax: `str | None`, `tuple[int, Path]`
- Return type annotations on all functions
- Argument type annotations used consistently

## Code Style

**Formatting:**
- Line length: No hard limit observed, but lines stay under ~100 characters
- Indentation: 4 spaces
- Strings: Double quotes preferred (`"string"` not `'string'`)
- Imports: Grouped (standard lib, then third-party, then local)

**Linting:**
- No linting or code quality tool configured (no `.pylintrc`, `pyproject.toml`, or `.flake8` detected)
- Code follows PEP 8 style conventions by convention, not enforcement
- No pre-commit hooks enforcing style

## Import Organization

**Order:**
1. `__future__` annotations (enables Python 3.10-style type hints): `from __future__ import annotations`
2. Standard library: `argparse`, `subprocess`, `sys`, `tempfile`, `urllib.*`, `pathlib.Path`
3. Third-party: `pypdf`, `fal_client`, `requests`

**Path Aliases:**
- No path aliases or import remapping used
- Relative imports not used; all imports are absolute
- All three-letter scripts import at the module level

## Error Handling

**Patterns:**
- Exit early with `sys.exit()` for configuration/setup errors: `sys.exit("Could not find Google Chrome/Chromium.")`
- Raise `ValueError` for invalid input (e.g., missing prompt marker): `raise ValueError(f"No '{PROMPT_MARKER}' marker found in {md_path.name}")`
- Try/except for network operations with fallback mechanism:
  - `urllib.error.URLError` caught and falls back to `curl` in `build/build-pdf.py`
  - `requests.get()` with `.raise_for_status()` in `grok/generate-panels.py`
- Exception details printed to `stderr` when recoverable: `print(f"...", file=sys.stderr)`
- `raise SystemExit()` used in `if __name__ == "__main__"` block instead of `sys.exit(main())`

## Logging

**Framework:** console only — no logging library used

**Patterns:**
- `print()` to stdout for normal progress: `print(f"page-{n}: saved -> {shown}")`
- `print(file=sys.stderr)` for warnings and non-fatal errors: `print(f"urllib download failed ({exc.reason}); falling back to curl ...", file=sys.stderr)`
- Informative messages with context: `print(f"Generating {len(targets)} panel(s) from {pages_dir.name} with {args.model} ({opts['image_size']}) -> {out_dir} ...")`
- Status reports use consistent prefixes: `page-{n}: exists, skipping`, `page-{n}: FAILED --`

## Comments

**When to Comment:**
- Function-level docstrings are required and comprehensive
- Inline comments used only for non-obvious logic or workarounds
- Complex regexes and string parsing explained (e.g., stem parsing in `page_files()`)
- Why a fallback exists is explained: `"Isolated profile so we never attach to a Chrome the user already has open..."`

**JSDoc/TSDoc:**
- Module docstrings provided at file top (PEP 257 style):
  - Explains script purpose
  - Lists usage examples with commands
  - Documents key environment variables
- Function docstrings (docstrings, no type comments):
  - Single-line for simple functions: `"""Fall back to system curl..."""`
  - Multi-line with explanation for complex logic
  - Document exceptions raised, e.g., `ValueError` in `extract_prompt()`

## Function Design

**Size:** Functions are concise (10–40 lines typical)
- `find_root()`: 4 lines
- `render_front_pdf()`: ~20 lines (calls subprocess, checks result)
- `generate_one()`: ~12 lines (extract, call API, save)

**Parameters:**
- Positional parameters ordered: required first, then Path/file arguments, then options
- Type hints on all: `def generate_one(n: int, md_path: Path, model: str, opts: dict, extra: dict, out_dir: Path)`
- Dict/kwargs used for model-specific options to avoid parameter explosion: `opts`, `extra` in `generate-panels.py`

**Return Values:**
- All functions have explicit return types: `-> Path`, `-> str`, `-> int`, `-> dict`, `-> tuple[int, Path]`
- Functions return meaningful values (paths, URLs, page numbers) or exit early
- No bare `return` statements; implicit `None` only when appropriate

## Module Design

**Exports:**
- Scripts use `if __name__ == "__main__": raise SystemExit(main())` pattern
- Functions are defined in dependency order (helper functions first, `main()` last)
- No class definitions; scripts are procedural with module-level constants and functions

**Barrel Files:**
- Not applicable; no barrel exports or module aggregation
- Each script is self-contained (`build-pdf.py`, `generate-panels.py`)

---

*Convention analysis: 2026-06-24*
