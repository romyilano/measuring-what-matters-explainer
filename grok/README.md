# Panel generation via fal.ai

Automates the six explainer comic panels using the **fal.ai** API — **you pick the
image model id**. This is the same renderer shipped with the
`explainer-site-generator` skill (`scripts/generate_panels.py`); this copy is kept
in sync for this repo.

Each `docs/explainer-src/manga/<slug>/page-0N.md` already contains a fully
self-contained prompt (locked house style + recurring cast + panel script).
`generate-panels.py` extracts the prompt body, sends one request per page, and
saves the result to `docs/panels/page-N.png` — the exact names the site expects.

## Setup

```bash
pip install -r grok/requirements.txt
export FAL_KEY="..."          # from https://fal.ai/dashboard/keys
                             # (or put FAL_API_KEY=... in ./.env.local)
```

## Choose a model

```bash
python grok/generate-panels.py --list-models     # curated suggestions
```

| Model id | Why |
| --- | --- |
| `openai/gpt-image-2` (default) | Best prompt adherence + legible in-image text |
| `fal-ai/flux-pro/v1.1` | Fast, strong ink/line editorial look |
| `fal-ai/recraft-v3` | Editorial illustration style control |
| `fal-ai/ideogram/v3` | Best when captions live inside the art |

Any valid fal.ai endpoint slug works.

## Run

```bash
python grok/generate-panels.py                          # all missing pages -> docs/panels
python grok/generate-panels.py --model fal-ai/flux-pro/v1.1
python grok/generate-panels.py --page 1                 # smoke-test one page first
python grok/generate-panels.py --force                  # regenerate everything
python grok/generate-panels.py --quality medium         # cheaper GPT-Image-2 tier
python grok/generate-panels.py --image-size portrait_16_9
python grok/generate-panels.py --arg guidance_scale=3.5 # model-specific knob
python grok/generate-panels.py --out-dir docs/panels-flux  # A/B without overwriting
```

Defaults: `openai/gpt-image-2`, `portrait_4_3`, `quality=high`, PNG, output to
`docs/panels/`. The manga project is auto-detected when there's only one; pass
`--slug <name>` if there are several.

## Notes

- **Character consistency:** independent API calls don't share memory, so the
  full cast description is baked into every page prompt. Watch for Dana/Theo
  drift across pages; regenerate individual pages with `--page N --force`.
- **Cost:** GPT-Image-2 bills per token; use `--quality medium` while iterating.
- **Model args differ:** non-`openai/*` models ignore `--quality`; use `--arg
  key=value` for anything model-specific.
- After rendering, update each page's `status` to `rendered` in
  `manga/construct-validity/manifest.md`.
