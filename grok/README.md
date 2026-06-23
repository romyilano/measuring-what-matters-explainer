# Panel generation via fal.ai

Automates the six explainer comic panels using the **fal.ai** API
(model `openai/gpt-image-2`), replacing the manual paste-into-ChatGPT loop.

Each `docs/explainer-src/manga/construct-validity/page-0N.md` already contains a
fully self-contained prompt (locked house style + recurring cast + panel
script). `generate-panels.py` extracts the prompt body, sends one request per
page, and saves the result to `docs/panels/page-N.png`.

## Setup

```bash
pip install -r grok/requirements.txt
export FAL_KEY="..."          # from https://fal.ai/dashboard/keys
```

## Run

```bash
python grok/generate-panels.py                 # all missing pages
python grok/generate-panels.py --page 1         # smoke-test one page first
python grok/generate-panels.py --force          # regenerate everything
python grok/generate-panels.py --quality medium # cheaper tier while iterating
python grok/generate-panels.py --image-size portrait_16_9
python grok/generate-panels.py --out-dir docs/panels-gpt # custom output dir
```

Defaults: `openai/gpt-image-2`, `portrait_4_3`, `quality=high`, PNG,
output to `docs/explainer-src/manga/construct-validity/grok/`.

## Compare two models side by side

`--out-dir` keeps each model's output separate so they don't overwrite:

```bash
python grok/generate-panels.py --force --out-dir docs/panels-gpt
python grok/generate-panels.py --force --model fal-ai/grok-... --out-dir docs/panels-grok
```

## Notes

- **Character consistency:** independent API calls don't share memory, so the
  full cast description is baked into every page prompt. Watch for Dana/Theo
  drift across pages; regenerate individual pages with `--page N --force`.
- **Cost:** GPT-Image-2 bills per token; use `--quality medium` while iterating.
- After rendering, update each page's `status` to `rendered` in
  `manga/construct-validity/manifest.md`.
