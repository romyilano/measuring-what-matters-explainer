# External Integrations

**Analysis Date:** 2026-06-24

## APIs & External Services

**Text-to-Image Generation:**
- fal.ai - Generates comic book panels from markdown prompts
  - SDK/Client: `fal-client` package
  - Auth: `FAL_KEY` env var (or `FAL_API_KEY`, `FAL_API_SECRET`)
  - Usage: `grok/generate-panels.py` subscribes to configurable image models
  - Models supported: `openai/gpt-image-2` (default), `fal-ai/flux-pro/v1.1`, `fal-ai/recraft-v3`, `fal-ai/ideogram/v3`, others

**arXiv Academic Papers:**
- arXiv.org - Hosts the source paper "Measuring what Matters: Construct Validity in LLM Benchmarks"
  - Paper ID: `2511.04703`
  - PDF endpoint: `https://arxiv.org/pdf/2511.04703`
  - Usage: Downloaded on-demand by `build/build-pdf.py:194-207` during PDF assembly
  - Fallback: System `curl` if urllib SSL fails

**Web Fonts:**
- Google Fonts - Typefaces for rendered output
  - Fonts: `Fraunces` (serif, editorial), `Newsreader` (serif, body text)
  - Endpoint: `https://fonts.googleapis.com`, `https://fonts.gstatic.com`
  - Preconnect hints in `docs/index.html:13-15`
  - Used only in static HTML rendering + PDF cover generation

## Data Storage

**Databases:**
- None

**File Storage:**
- Local filesystem only
  - Comic panels: `docs/panels/page-{1-6}.png` (generated)
  - Final PDF: `docs/construct-validity.pdf` (generated)
  - Source markdown: `documentation/explainer-src/manga/construct-validity/page-{01-06}.md`
  - Static site: `docs/index.html`

**Caching:**
- None (Python scripts regenerate artifacts on demand)

## Authentication & Identity

**Auth Provider:**
- None for the final deliverable (static HTML)
- Development only: fal.ai API key required (`FAL_KEY` env var)
  - Used in `grok/generate-panels.py:251-255` with validation
  - Lazy import pattern: dependencies only loaded when actually generating panels

## Monitoring & Observability

**Error Tracking:**
- None

**Logs:**
- Python scripts write to stdout/stderr
  - `grok/generate-panels.py` reports generation progress and model cost info
  - `build/build-pdf.py` reports Chrome headless rendering + PDF output status

## CI/CD & Deployment

**Hosting:**
- GitHub Pages (static site)
  - URL: `https://romyilano.github.io/measuring-what-matters-explainer/`
  - Source: `docs/` directory

**CI Pipeline:**
- None detected (manual script invocation only)

## Environment Configuration

**Required env vars (for development only):**
- `FAL_KEY` or `FAL_API_KEY` - fal.ai authentication (see `.env.local` mention)
- `FAL_IMAGE_MODEL` (optional) - Override default image model; defaults to `openai/gpt-image-2`

**Optional env vars:**
- `FAL_AI_KEY` - Alternative alias for `FAL_KEY`

**Secrets location:**
- `.env.local` - Local environment file with FAL credentials (file present; contents not revealed per policy)
- Reference: `grok/generate-panels.py:100-115` (dotenv loading and alias handling)

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## API Request Patterns

**fal.ai Panel Generation:**
- Endpoint: Configurable fal.ai text-to-image model (e.g., `openai/gpt-image-2`)
- Call pattern: `fal_client.subscribe(model, arguments=...)` at `grok/generate-panels.py:190`
- Arguments passed per model: `image_size` (default: `portrait_4_3`), `quality` (GPT-Image-2 only), model-specific `--arg` overrides
- Response: JSON with image URL extracted at `grok/generate-panels.py:180-181`
- Downloaded via `requests.get(url)` at `grok/generate-panels.py:193`

**arXiv Paper Download:**
- URL construction: `https://arxiv.org/pdf/{ARXIV_ID}` (ID hardcoded as `2511.04703`)
- User-Agent: `paper-reading-club/1.0 (research)` for politeness
- Fallback: System curl with `-fsSL` flag if Python urllib SSL fails
- Timeout: 60 seconds

---

*Integration audit: 2026-06-24*
