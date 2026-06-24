# Codebase Concerns

**Analysis Date:** 2026-06-24

## Tech Debt

### External Dependency on fal.ai API

**Issue:** The comic panel generation is entirely dependent on the fal.ai API (`grok/generate-panels.py`). If the API changes endpoints, pricing, or closes, the entire pipeline breaks with no fallback.

**Files:** `grok/generate-panels.py`, `grok/requirements.txt`

**Impact:** 
- Cannot regenerate panels without API access and valid API key
- No local model fallback or offline option
- Cost is hidden behind per-token billing (GPT-Image-2) or per-request (Flux)
- Different models have different argument schemas; switching models requires code changes

**Fix approach:** 
- Document exact model specs and pricing at the time of rendering
- Archive rendered PNGs in git so rebuilds don't require regeneration
- Consider implementing a local Stable Diffusion fallback for development/demo purposes
- Add model version pinning and deprecation warnings

### Hard-coded File Paths in Path Resolution

**Issue:** The build scripts use `find_root()` logic that walks up the directory tree until it finds a specific directory marker (`docs/index.html` or `documentation/explainer-src`). This is fragile if the directory structure changes.

**Files:** `build/build-pdf.py` (lines 44-48), `grok/generate-panels.py` (lines 60-65)

**Impact:**
- If anyone renames `docs/` or `documentation/` directories, scripts silently fail or use wrong paths
- No validation that found paths actually exist before proceeding
- Unclear error messages if the expected directory structure is missing

**Fix approach:**
- Validate directory structure explicitly at startup with clear error messages
- Document the required directory structure in a top-level STRUCTURE.md or setup guide
- Add optional `--root` parameter to override auto-detection
- Add sanity checks after root detection to verify expected subdirectories

### Undocumented Path Migration (Renamed docs/ to documentation/)

**Issue:** The codebase underwent a reorganization (git status shows renames from `docs/` to `documentation/`), but the scripts still contain stale path references mixed with updated ones.

**Files:** `grok/generate-panels.py` (partially updated in pending changes), `grok/README.md` (pending update)

**Impact:**
- Both path schemas coexist in comments and docstrings, creating confusion
- New users see conflicting documentation about where files live
- The migration is not fully committed; pending changes are still staged

**Fix approach:**
- Complete the directory rename and commit it
- Update all docstrings and README files consistently
- Add a changelog entry explaining the migration
- Verify both scripts reference `documentation/` throughout

## Dependencies at Risk

### Chrome/Chromium Runtime Dependency

**Risk:** The PDF builder (`build/build-pdf.py`) requires Google Chrome or Chromium to be installed locally and available at one of several hard-coded paths. The script will exit if none are found.

**Files:** `build/build-pdf.py` (lines 35-60)

**Impact:**
- CI/CD pipelines need Chrome installed in the environment
- Different platforms (Linux, macOS, Windows) have different default Chrome paths
- If a user's Chrome installation is in a non-standard location, the script fails with minimal guidance
- macOS M1/M2 native builds may not be in the expected `Applications` path

**Current mitigation:** Hard-coded list of 5 candidate paths; users can modify `CHROME_CANDIDATES`

**Recommendations:**
- Add `--chrome` flag to specify custom Chrome path
- Check for Chrome in PATH before trying fixed locations
- Provide clear error message with user's actual Chrome path (can be found via `which google-chrome` or `which chromium`)
- Document platform-specific setup in README

### pypdf Version Pinning Missing

**Risk:** `build/build-pdf.py` imports `pypdf` without a pinned version in requirements. The API or behavior could change in new versions.

**Files:** `build/build-pdf.py` (line 30), `grok/requirements.txt` (incomplete)

**Impact:**
- PDF merging behavior could change if pypdf releases a breaking update
- No guarantee that old PDFs can be regenerated with new library versions
- The project has no `build/requirements.txt` or dependency manifest for build tools

**Fix approach:**
- Create `build/requirements.txt` with pinned versions: `pypdf>=4.0.0,<5.0.0` (or equivalent)
- Test with multiple pypdf versions to establish compatibility
- Document minimum Python version (likely 3.8+)

## Scaling Limits

### Large PNG Panel Files

**Current capacity:** Six 3–3.2 MB PNG files (total ~18.8 MB in `docs/panels/`)

**Limit:** 
- File size grows quadratically with image resolution
- HTTP serving of multiple 3 MB files per page load is slow on low-bandwidth connections
- Git repository bloat: 18.8 MB is significant for a small project
- No image compression, format conversion, or responsive image serving

**Scaling path:**
- Switch panels to WebP or AVIF format (40–60% size reduction)
- Generate multiple resolutions (e.g., 1x, 2x, 3x) with srcset
- Compress PNG with `pngquant` or `oxipng` during build
- Host images on a CDN or separate asset server, not in git
- Add CI/CD step to validate image sizes and warn on bloat

## Fragile Areas

### PDF Build Process (Chrome-Dependent)

**Files:** `build/build-pdf.py` (lines 163–182)

**Why fragile:**
- Launches headless Chrome with specific flags that may be deprecated or break in new Chrome versions
- Uses `--virtual-time-budget=15000` to control page load timing; timeout is magic number with no documentation
- No retry logic if Chrome crashes or times out
- CSS font loading (`fonts.googleapis.com`) is assumed to work; network failure is unhandled

**Safe modification:**
- Add logging to see what Chrome is doing before it fails
- Increase `--virtual-time-budget` and test with real network latency
- Wrap subprocess call in timeout with explicit error handling
- Test locally before committing changes that add custom `<style>` or fonts

**Test coverage:** None detected; no test directory or test files

### Image Generation Pipeline

**Files:** `grok/generate-panels.py` (lines 184–196)

**Why fragile:**
- Calls `fal_client.subscribe()` which blocks until image generation completes (can take minutes)
- No timeout or cancellation logic; if fal.ai hangs, the whole run hangs
- Result shape varies by model; `image_url_from_result()` attempts to extract image from unpredictable JSON (lines 174–181)
- Raises `ValueError` if image URL can't be found, crashing the entire batch
- No retry on transient failures (network blip, API hiccup)

**Safe modification:**
- Add explicit timeout: `fal_client.subscribe(..., timeout=300)` or similar
- Wrap `generate_one()` in retry logic with exponential backoff for transient errors
- Log the full result JSON if image extraction fails, for debugging
- Add `--timeout` and `--max-retries` CLI arguments

**Test coverage:** None detected

## Missing Critical Features

### Build Reproducibility

**Problem:** There is no way to reproduce the exact PDF output from source if:
- fal.ai changes its image generation
- Chrome updates rendering behavior
- Google Fonts become unavailable
- The paper PDF at arXiv changes version

**Blocks:** Archiving, verification, long-term preservation of the deliverable

**Recommendation:** 
- Commit rendered panels to git (or store in git LFS)
- Pin the arXiv paper ID or download and commit the paper PDF
- Document the exact environment (Chrome version, Python version) used to build
- Add a checksum or manifest file for the final PDF

### Error Recovery and Reporting

**Problem:** If the build or generation process fails partway through (e.g., page 3 of 6 fails), there's no way to resume or see which pages succeeded and which didn't.

**Impact:**
- Full re-run is required, wasting API quota and time
- No audit trail of what was generated when
- Hard to debug which page caused the problem

**Recommendation:**
- Add a `--resume` flag to skip already-generated pages
- Write a manifest file recording which pages were generated and when
- Add `--verbose` logging with timestamps
- Save intermediate artifacts (front.pdf) for inspection

### Version Control of Generated Assets

**Problem:** The PDF output (`docs/construct-validity.pdf`) and panel PNGs are generated files but may be committed to git. There's no `.gitkeep` or `/.gitignore` to clarify whether they're version-controlled.

**Impact:**
- Repository size grows with every build
- Unclear if builds should be part of CI or manual
- Collaborators may not know whether to commit or ignore generated files

**Recommendation:**
- Either (a) commit `.gitignore` entries for generated files and document how to rebuild, or (b) commit them explicitly with a note in README explaining they're checked in for convenience
- Add a `Makefile` or `build.sh` script to document the build process
- Include generated file checksums in a manifest if they're committed

## Test Coverage Gaps

### No Unit Tests

**What's not tested:** 
- Path resolution logic in both `find_root()` functions
- HTML generation and CSS in `build-pdf.py`
- Prompt extraction and model argument building in `generate-panels.py`
- Error conditions (missing files, malformed prompts, API failures)

**Files:** All Python files lack test coverage

**Risk:** 
- Breaking changes to path logic go undetected until run-time (in production)
- CSS/HTML issues only appear when Chrome renders (late feedback)
- Prompt extraction assumes well-formed Markdown; malformed input crashes silently
- No tests for the fallback `_download_curl()` function

**Priority:** Medium — these are small scripts, but path logic and API error handling should be tested

### No Integration Tests

**What's not tested:**
- End-to-end PDF build with real Chrome (only tested manually)
- Full image generation pipeline with fal.ai
- Concurrent panel generation under thread pool (race conditions)

**Files:** No test directory

**Risk:**
- Chrome rendering changes are discovered after deployment
- Concurrent downloads may corrupt images or create duplicates
- Integration with PDF merging (pypdf) is untested

### No Regression Tests for Output Quality

**What's not tested:**
- Panel images render without artifacts or truncation
- PDF page breaks occur at correct boundaries (worksheet pages)
- Font embedding doesn't fail silently
- QR code generation produces correct link

**Risk:** Silent quality degradation — file builds successfully but output is wrong

**Priority:** Low for small projects, but should be considered before heavy distribution

---

*Concerns audit: 2026-06-24*
