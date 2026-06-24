<!-- refreshed: 2026-06-24 -->
# Architecture

**Analysis Date:** 2026-06-24

## System Overview

This is a **whitepaper explainer project** — a multi-format educational asset generator that transforms an academic paper (arXiv:2511.04703 on construct validity in LLM benchmarks) into an interactive six-page comic, a downloadable PDF, and discussion resources.

```text
┌─────────────────────────────────────────────────────────────┐
│                    Explainer Site Layer                      │
│         `docs/index.html` — Interactive web viewer          │
│  - Responsive masthead + six comic panels w/ captions        │
│  - Cast appendix + philosophy diagrams + links               │
│  - Direct links to PDF download and arXiv paper              │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┬────────────────┐
        ▼                         ▼                ▼
┌──────────────────┐    ┌──────────────────┐  ┌──────────────┐
│ PDF Build Layer  │    │ Panel Generation │  │ Source Config│
│ `build/`         │    │ Layer `grok/`    │  │ `documentation/`
└──────────────────┘    └──────────────────┘  └──────────────┘
        │                        │
        ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Asset & Data Layer                              │
│  `docs/panels/*.png` — Six comic pages (rendered images)    │
│  `docs/construct-validity.pdf` — Assembled PDF              │
│  `documentation/explainer-src/manga/construct-validity/`    │
│  └─ Page prompts, character sheet, manifest, notes          │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  fal.ai Text-to-Image API                                   │
│  (Renders prompts into six comic panels)                    │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Explainer Site** | Present comic, discussion resources, navigation; downloadable PDF link | `docs/index.html` |
| **Panel Generation** | Convert page-NN.md prompts into PNG images via fal.ai API | `grok/generate-panels.py` |
| **PDF Assembly** | Merge HTML-rendered cover + comic panels + source paper into PDF | `build/build-pdf.py` |
| **Source Manifest** | Define page order, dependencies, narrative flow, character definitions | `documentation/explainer-src/manga/construct-validity/manifest.md` |
| **Page Prompts** | Six self-contained image prompts (page-01.md through page-06.md) | `documentation/explainer-src/manga/construct-validity/page-0N.md` |
| **Character Sheet** | Recurring cast definition (Dana, Theo) — baked into every page prompt | `documentation/explainer-src/manga/construct-validity/character-sheet.md` |
| **Discussion Spike** | Curated talking points; maps paper concepts to vibe-coding practice | `spikes/construct-validity-in-vibe-coding.md` |

## Pattern Overview

**Overall:** Pipeline-based **multi-format asset generator** with single source of truth.

**Key Characteristics:**
- **Single source of truth:** Page prompts (page-01.md through page-06.md) are self-contained; they embed style, character definitions, and narrative without external dependencies
- **Staged pipeline:** Define → Render (fal.ai) → Assemble (PDF) → Publish (web)
- **Environment-driven:** Secrets (FAL_KEY) via .env; configuration via CLI flags
- **Fallback-safe:** PDF generation has curl fallback for arXiv download; Chrome detection for headless rendering

## Layers

**Source Definition Layer:**
- Purpose: Define explainer structure, character voice, page narrative, and image prompts
- Location: `documentation/explainer-src/manga/construct-validity/`
- Contains: Manifest, character sheet, six page prompts (markdown), notes
- Depends on: External visual reference (no code dependencies)
- Used by: Panel generation (reads page-0N.md), PDF builder (references page order)

**Panel Generation Layer:**
- Purpose: Transform text prompts into image assets using fal.ai API
- Location: `grok/generate-panels.py`
- Contains: Prompt extraction, fal.ai client integration, concurrent batch rendering, model selection
- Depends on: fal.ai API key (env), source page prompts, Python 3.10+ (concurrent.futures)
- Used by: Manual invocation; output feeds PDF builder

**PDF Assembly Layer:**
- Purpose: Render HTML cover page with headless Chrome, merge with comic panels and source paper
- Location: `build/build-pdf.py`
- Contains: HTML template (cover + worksheets + divider), Chrome invocation, PDF merging logic, arXiv download with curl fallback
- Depends on: Google Chrome/Chromium, pypdf (PDF merging), system curl (fallback download)
- Used by: Manual invocation; output is final deliverable

**Web Publication Layer:**
- Purpose: Serve interactive comic with responsive typography, cast appendix, download links
- Location: `docs/index.html` (generated/static)
- Contains: HTML structure, embedded CSS (color system, responsive layout), Google Fonts, asset references
- Depends on: `docs/panels/*.png` (comic images), `docs/construct-validity.pdf`, `docs/qr.png`
- Used by: Published at GitHub Pages; no runtime dependencies

**Discussion/Learning Layer:**
- Purpose: Bridge paper concepts to lived experience; discussion prompts
- Location: `spikes/construct-validity-in-vibe-coding.md`
- Contains: Failure mode mapping, vibe-coding analogs, discussion questions
- Depends on: No code/asset dependencies; standalone reference
- Used by: Paper reading club participants; living document

## Data Flow

### Primary Flow: Explainer Creation

1. **Define** — Write page prompts in `documentation/explainer-src/manga/construct-validity/page-0N.md` with locked style block, character descriptions, and narrative
   - Each page is self-contained; style + cast baked in
   
2. **Generate panels** — Run `python grok/generate-panels.py`
   - Reads `.env.local` or `FAL_KEY` env var
   - Extracts image prompts from page-0N.md files
   - Calls fal.ai API (configurable model; default: openai/gpt-image-2)
   - Saves results to `docs/panels/page-N.png`
   
3. **Build PDF** — Run `python build/build-pdf.py`
   - Renders `docs/index.html` structure as front matter via headless Chrome
   - Includes cover, six panels, two worksheets, divider, source paper
   - Downloads arXiv PDF (2511.04703) or accepts `--paper` local path
   - Merges all pages with pypdf
   - Writes `docs/construct-validity.pdf`
   
4. **Publish web** — `docs/index.html` already static
   - Committed to repo; served by GitHub Pages
   - References `docs/panels/*.png` and `docs/construct-validity.pdf`
   - No build step required (HTML is hand-authored)

### Secondary Flow: Model Selection & Iteration

- User runs `python grok/generate-panels.py --list-models` to see curated options
- Picks model: `--model fal-ai/flux-pro/v1.1` or similar
- Can regenerate single page: `--page 3 --force`
- Can A/B test: `--out-dir docs/panels-flux` (preserves originals)
- Updates `manifest.md` status column after rendering complete

**State Management:**
- **No stateful backend.** Each run is independent.
- **Prompt versioning** via git (page-0N.md files tracked)
- **Manifest metadata** (status: pending/rendered) is manually updated after generation
- **Environment config** via `.env.local` (not committed; local only)

## Key Abstractions

**The Locked Style Block:**
- Purpose: Ensures visual consistency across all six panels despite independent API calls
- Examples: `documentation/explainer-src/manga/construct-validity/page-01.md` (lines 27-40 of prompt)
- Pattern: Narrative description + style directives copied verbatim into every fal.ai call
  - Specifies ligne-claire line art, muted palette, New Yorker deadpan tone
  - Guards against model drift between pages

**The Self-Contained Page Prompt:**
- Purpose: Make each page independent (API has no memory between calls)
- Examples: `page-01.md`, `page-02.md`, ..., `page-06.md`
- Pattern: Full character descriptions (Dana, Theo) + locked style + narrative prompt in one markdown block
  - Prevents character drift when regenerating individual pages
  - Enables swapping models or quality tiers per page

**The Manifest:**
- Purpose: Single source of truth for page order, narrative flow, and metadata
- Examples: `documentation/explainer-src/manga/construct-validity/manifest.md`
- Pattern: Concept table mapping page # → narrative purpose → visual metaphor → status
  - Status field (pending/rendered) tracks which pages have been generated
  - Concept ordering (1–6) defines learning progression

**The Worksheet Template:**
- Purpose: Embed learning retention checkpoints in PDF
- Examples: `build/build-pdf.py` (lines 134–153 of HTML)
- Pattern: Two recall worksheets (whiteboard sketch + mind-map) between comic and paper
  - Not code; embedded CSS in PDF builder
  - Designed for hand annotation

## Entry Points

**User: Generate Panels**
- Location: `grok/generate-panels.py` (command-line CLI)
- Triggers: `python grok/generate-panels.py [options]`
- Responsibilities:
  - Parse CLI (--model, --page, --force, --list-models, --slug, etc.)
  - Load `.env.local` for FAL_KEY
  - Discover manga projects under `documentation/explainer-src/manga/`
  - Extract prompts from page-0N.md files
  - Call fal.ai for each page (sequential or concurrent via ThreadPoolExecutor)
  - Save PNG results to output directory (default: `docs/panels/`)

**User: Build PDF**
- Location: `build/build-pdf.py` (command-line CLI)
- Triggers: `python build/build-pdf.py [--paper local.pdf]`
- Responsibilities:
  - Find project root (walk up until `docs/index.html` found)
  - Render HTML cover/worksheets/divider via headless Chrome
  - Download arXiv PDF (2511.04703) or use supplied `--paper` path
  - Merge all PDFs (front HTML + comic panels + paper) with pypdf
  - Write `docs/construct-validity.pdf`

**Browser: View Explainer**
- Location: `docs/index.html` (static file)
- Triggers: Browse to GitHub Pages URL or open locally
- Responsibilities:
  - Render responsive masthead with title, standfirst, credit
  - Lazy-load six comic panel images with fallback placeholders
  - Display cast appendix table and phenomenon/task/score diagram
  - Provide download + read paper buttons

**Reader: Reference Discussion**
- Location: `spikes/construct-validity-in-vibe-coding.md`
- Triggers: Opened from README or shared in Paper Reading Club
- Responsibilities:
  - Map paper's eight failure modes to vibe-coding practice
  - Provide discussion prompts (8 rows + 4 topic starter questions)
  - Standalone; no dependencies

## Architectural Constraints

- **Environment:** Python 3.10+ (concurrent.futures); Chrome/Chromium installed; fal.ai API key required for panel generation
- **Secrets:** FAL_KEY (or FAL_API_KEY, FAL_AI_KEY aliases) must be in environment; stored in `.env.local` (not committed)
- **Artifacts:** PNG panels must be committed to `docs/panels/` to render the site (browser cannot re-render on demand)
- **Static site:** `docs/` is published via GitHub Pages; no server-side rendering
- **Single model per run:** `--model` flag applies to all pages in one invocation; A/B testing requires separate `--out-dir` runs
- **No data contamination checks:** fal.ai doesn't cross-reference prior runs; character consistency depends on locked style block in prompts

## Anti-Patterns

### Hardcoded Model Endpoints

**What happens:** Someone embeds `openai/gpt-image-2` directly in `generate-panels.py` logic instead of using `--model` flag or env var.

**Why it's wrong:** If fal.ai deprecates an endpoint, every page prompt breaks simultaneously. The model choice should be runtime-selectable so users can test alternatives (Flux, Recraft, etc.) without code edits.

**Do this instead:** Use `DEFAULT_MODEL = os.environ.get("FAL_IMAGE_MODEL", "openai/gpt-image-2")` (as in `grok/generate-panels.py` line 40) and pass `--model` to override. Never embed endpoint names in page prompts.

### Fragmented Prompt Storage

**What happens:** Style block lives separately from narrative; character descriptions scattered across files; each page prompt imports from shared includes.

**Why it's wrong:** Splits the source of truth. If Dana's description changes, all pages must be updated in concert. Increases risk of drift (some pages get updated, others don't).

**Do this instead:** Every page-0N.md is self-contained. Bake style block + character sheet + narrative into one file (as in `page-01.md` through `page-06.md`). Accept the redundancy; it enables independent rendering and regeneration.

### Manual PDF Merging Without Checksums

**What happens:** Run `build-pdf.py`, it merges PDFs, but there's no validation that all pages made it into the final PDF.

**Why it's wrong:** A silent merge error could drop a page and ship an incomplete PDF undetected.

**Do this instead:** `build-pdf.py` already does this (line 228): `PdfReader(str(OUT_PDF)).pages` — it reads the output and prints the page count. Ensures transparency on what shipped.

## Error Handling

**Strategy:** Explicit failures with actionable error messages; graceful fallbacks for external services.

**Patterns:**
- **Chrome not found** → Print list of search paths, exit with helpful error (line 60: `sys.exit("Could not find...")`)
- **arXiv download fails** → Fall back to system curl with user-agent header (line 205: try urllib, except URLError → _download_curl)
- **fal.ai API error** → Print HTTP status + error body; exit (caller must retry with correct FAL_KEY)
- **Manga project ambiguity** → If multiple projects under `documentation/explainer-src/manga/`, error asks user to pick with `--slug` (line 97 in grok/generate-panels.py)

## Cross-Cutting Concerns

**Environment Configuration:** All secrets via env vars or `.env.local` (never hardcoded). `.env.local` is in `.gitignore` to prevent leaks.

**Logging:** No structured logging; relies on print statements with context (e.g., "Wrote docs/construct-validity.pdf (42 pages)."). Sufficient for CI/command-line use.

**API Key Management:** fal.ai key can come from three env var names (FAL_KEY, FAL_API_KEY, FAL_AI_KEY) for flexibility. Default site behavior (no API calls) if key is absent.

**Concurrency:** Panel generation uses `concurrent.futures.ThreadPoolExecutor` for batch rendering (line 32 in grok/generate-panels.py). One thread per page; threads share API quota.

---

*Architecture analysis: 2026-06-24*
