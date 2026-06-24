# Technology Stack

**Analysis Date:** 2026-06-24

## Languages

**Primary:**
- Python 3.14+ - Build and content generation scripts

**Secondary:**
- HTML - Static site served from `docs/`
- CSS - Embedded in HTML and build output

## Runtime

**Environment:**
- Python 3.14.6 (macOS)

**Package Manager:**
- pip

**Lockfile:**
- `grok/requirements.txt` - Python dependencies for image generation
- `build/` - No separate lock file; imports use stdlib + external deps

## Frameworks

**PDF Generation:**
- `pypdf` - PDF merging and manipulation (`build/build-pdf.py`)

**Image Generation:**
- `fal-client` - fal.ai image API client for text-to-image panel generation
- `requests` - HTTP library for downloading generated images

**Build/Dev:**
- Google Chrome/Chromium - Headless renderer for converting HTML → PDF cover pages (`build/build-pdf.py`)

## Key Dependencies

**Critical:**
- `fal-client` - Enables automated comic panel generation via fal.ai API. Used in `grok/generate-panels.py` with lazy import at `grok/generate-panels.py:185`.
- `requests` - HTTP client for downloading PNG images from fal.ai after generation. Used in `grok/generate-panels.py:186`.
- `pypdf` - PDF manipulation library for merging rendered cover/comic pages with arXiv paper PDF. Imported in `build/build-pdf.py:30`.

**Infrastructure:**
- None - external APIs handled via direct HTTP + SDK clients.

## Configuration

**Environment:**
- `.env.local` - Stores `FAL_KEY` or `FAL_API_KEY` for fal.ai authentication. Reference: `grok/generate-panels.py:100-115` (dotenv loading logic).
- Environment variable fallback: `$FAL_KEY`, `$FAL_API_KEY`, or `$FAL_IMAGE_MODEL` for model selection.

**Build:**
- No static build config files (tsconfig, webpack, etc.)
- Python scripts use argparse for CLI configuration
- Chrome search path hardcoded in `build/build-pdf.py:35-40` with platform-specific candidates

## Platform Requirements

**Development:**
- Python 3.14+
- Google Chrome or Chromium (for headless PDF rendering)
- pip + internet access for dependency installation
- FAL.ai account + API key for image generation

**Production:**
- Static site hosting (GitHub Pages) — `docs/` directory served as-is
- No backend server required
- Downloadable PDF artifact (`docs/construct-validity.pdf`)

---

*Stack analysis: 2026-06-24*
