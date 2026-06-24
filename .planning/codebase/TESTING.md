# Testing Patterns

**Analysis Date:** 2026-06-24

## Test Framework

**Status:** Not detected

No test framework is present in this codebase. There are:
- No test files (`*_test.py`, `test_*.py`, `*_spec.py`)
- No test configuration files (`pytest.ini`, `setup.cfg`, `tox.ini`)
- No test dependencies in requirements files
- No CI/CD test pipeline (GitHub Actions, Jenkins, etc.)

This is a **documentation/build automation project**, not a library or application with production code requiring unit tests.

## Manual Testing Approach

The two scripts in this codebase (`build/build-pdf.py` and `grok/generate-panels.py`) are **command-line tools** that are tested by running them manually:

**`build/build-pdf.py`:**
- Run locally: `python build/build-pdf.py` (downloads arXiv paper, renders HTML via Chrome, merges PDFs)
- Run with local paper: `python build/build-pdf.py --paper some.pdf` (validates the PDF merge path without network)
- Success criterion: Output file created at `docs/construct-validity.pdf` and is valid PDF

**`grok/generate-panels.py`:**
- List available models: `python grok/generate-panels.py --list-models` (requires no API key, tests help text)
- Dry-run paths: Script checks for existing `page-N.png` files and skips if present (no --force); can run without API key to test arg parsing
- Full run with API: `python grok/generate-panels.py` (requires FAL_KEY env var, generates images via fal.ai)
- Test specific page: `python grok/generate-panels.py --page 3` (isolates failures to single panel)
- Force regenerate: `python grok/generate-panels.py --force` (overwrites existing cache)

## Error Handling in Scripts

Both scripts validate inputs and fail fast:

**Input validation:**
- `build-pdf.py`: Checks Chrome exists via `find_chrome()` before attempting render; exits if not found
- `generate-panels.py`: Validates FAL_KEY is set before querying API; exits with helpful message if missing
- `generate-panels.py`: Validates manga project directory exists if `--slug` is provided

**Fallback patterns:**
- `build-pdf.py`: Falls back to `curl` when `urllib` SSL verification fails (network resilience)
- `generate-panels.py`: Validates page-file naming format; skips malformed files silently

**Error reporting:**
- Non-fatal failures print to stderr with context: `print(f"page-{n}: FAILED -- {exc}", file=sys.stderr)`
- Partial successes are counted: `failures = 0` counter incremented on exception, script returns `1` if any failure occurred
- Final status reported: `Wrote {path} ({n} pages).`

## Exception Handling Patterns

**Network operations:**
```python
# build-pdf.py: urllib with fallback to curl
try:
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
except urllib.error.URLError as exc:
    print(f"urllib download failed ({exc.reason}); falling back to curl ...", file=sys.stderr)
    _download_curl(ARXIV_PDF_URL, dest)
```

**API calls with recovery:**
```python
# generate-panels.py: concurrent image generation with per-task error handling
with ThreadPoolExecutor(max_workers=min(6, len(targets))) as pool:
    futures = { pool.submit(...): n for n, p in targets }
    for fut in as_completed(futures):
        n = futures[fut]
        try:
            n, out_path = fut.result()
            print(f"page-{n}: saved -> {shown}")
        except Exception as exc:
            failures += 1
            print(f"page-{n}: FAILED -- {exc}", file=sys.stderr)
```

**Subprocess error handling:**
```python
# build-pdf.py: Chrome rendering
subprocess.run(
    [...],
    check=True, capture_output=True,  # Raises CalledProcessError on non-zero exit
)
if not front_pdf.exists():
    sys.exit("Chrome did not produce the front PDF.")  # Explicit check after success
```

## Concurrency & Threading

**Model:** `grok/generate-panels.py` uses concurrent image generation:
- `ThreadPoolExecutor` with `max_workers=min(6, len(targets))` (up to 6 concurrent API calls)
- `as_completed()` iterator processes results as they arrive (not in submission order)
- Per-task exception handling: one failure doesn't block others
- Aggregates failures and returns exit code `1` if any task failed

**No shared mutable state:** Each thread gets its own page number, path, and output directory; no locks needed.

## Testing Coverage

**Gaps:**
- No unit tests for path parsing (`extract_prompt()`, `page_files()`)
- No mocking of fal.ai API or urllib (would require test framework setup)
- No validation of PDF merge operation (only checked by file existence)
- HTML generation (`cover_and_comic_html()`) not validated; only tested by running full pipeline

**Why acceptable here:** Scripts are thin wrappers around external tools (Chrome, fal.ai, arXiv). The most critical logic is:
1. **Configuration management** (finding Chrome, loading .env, resolving paths) — tested implicitly by script running
2. **Error handling** (fallback to curl) — validated when network fails
3. **Concurrent API calls** (ThreadPoolExecutor) — validated by running the panel generation at scale (up to 6 pages in parallel)

## Dependencies & External APIs

**`build/build-pdf.py`:**
- External: Google Chrome or Chromium (via `subprocess` call)
- External: arXiv PDF server (via `urllib`)
- Internal: `pypdf` (for PDF merging)

**`grok/generate-panels.py`:**
- External: fal.ai API (via `fal_client` SDK)
- External: Image download via `requests`
- Internal: fal_client, requests (from `grok/requirements.txt`)

**Env variables:**
- `FAL_KEY` (or aliases `FAL_AI_KEY`, `FAL_API_KEY`) — required to call fal.ai
- Loaded from `.env.local`, `.env` in root directory (see `load_dotenv()` in `generate-panels.py`)

## How to Run Tests Manually

There are no automated tests, but you can validate the scripts:

```bash
# Test build-pdf.py
cd /path/to/repo
python build/build-pdf.py --help                    # Check arg parsing
python build/build-pdf.py --paper dummy.pdf 2>&1    # Test with missing file (expects error)
python build/build-pdf.py                           # Full run (requires Chrome + network)

# Test generate-panels.py
python grok/generate-panels.py --list-models        # No API key needed
python grok/generate-panels.py --help               # Check all flags
python grok/generate-panels.py --page 1             # Test single page (requires FAL_KEY)
python grok/generate-panels.py --force              # Regenerate all (requires FAL_KEY)
```

---

*Testing analysis: 2026-06-24*
