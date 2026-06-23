#!/usr/bin/env python3
"""Generate the explainer comic panels via fal.ai (text-to-image).

Each docs/explainer-src/manga/<slug>/page-0N.md already contains a fully
self-contained image prompt (locked house style + recurring cast + panel
script). This script extracts the prompt body and sends one request per page to
fal.ai, saving each result to the output dir as page-N.png — the exact names the
explainer site references (docs/panels/page-1.png ... page-6.png).

This replaces the manual paste-into-ChatGPT loop. The model is YOUR choice:
pass --model <fal endpoint slug> (or set $FAL_IMAGE_MODEL). Run --list-models to
see curated suggestions. Different models accept different arguments, so use
--arg key=value to pass anything model-specific.

Usage:
    pip install fal-client requests
    export FAL_KEY="<your fal.ai key>"
    python generate_panels.py                       # all missing pages -> docs/panels
    python generate_panels.py --force               # regenerate everything
    python generate_panels.py --page 3              # just page 3
    python generate_panels.py --list-models         # show curated model ids
    python generate_panels.py --model fal-ai/flux-pro/v1.1
    python generate_panels.py --slug raft           # pick the manga project
    python generate_panels.py --arg guidance_scale=3.5 --arg seed=42
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# fal_client + requests are imported lazily inside generate_one() so that
# --list-models and --help work without the deps installed.

# ---------------------------------------------------------------------------
# Default text-to-image endpoint. Override per run with --model / $FAL_IMAGE_MODEL.
DEFAULT_MODEL = os.environ.get("FAL_IMAGE_MODEL", "openai/gpt-image-2")

# Curated fal.ai text-to-image endpoints. These differ in argument schema and
# pricing — see --arg for model-specific knobs. Not exhaustive; any valid fal
# endpoint slug works.
SUGGESTED_MODELS = {
    "openai/gpt-image-2": "Best prompt adherence + legible in-image text. Bills per token; honors --quality.",
    "fal-ai/flux-pro/v1.1": "Fast, high-quality Flux Pro. Great ink/line editorial look.",
    "fal-ai/flux-pro/v1.1-ultra": "Higher-res Flux Pro Ultra; slower, pricier.",
    "fal-ai/flux/dev": "Cheaper Flux dev tier — good for iterating on composition.",
    "fal-ai/recraft-v3": "Strong illustration/editorial style control.",
    "fal-ai/ideogram/v3": "Best in-image typography if your captions live inside the art.",
}
# ---------------------------------------------------------------------------

PROMPT_MARKER = "Image Prompt:"
# fal_client authenticates via the FAL_KEY env var. Accept these aliases too.
FAL_KEY_ALIASES = ("FAL_KEY", "FAL_AI_KEY", "FAL_API_KEY")


def find_root(start: Path) -> Path:
    """Walk up from a starting dir until we find one containing docs/explainer-src."""
    for d in [start, *start.parents]:
        if (d / "docs" / "explainer-src").is_dir():
            return d
    return start


def resolve_root() -> Path:
    """Prefer the current working directory's repo, then this script's location."""
    cwd_root = find_root(Path.cwd())
    if (cwd_root / "docs" / "explainer-src").is_dir():
        return cwd_root
    return find_root(Path(__file__).resolve().parent)


def manga_projects(root: Path) -> list[Path]:
    """Every manga project dir under docs/explainer-src/manga/."""
    manga_root = root / "docs" / "explainer-src" / "manga"
    if not manga_root.is_dir():
        return []
    return sorted(p for p in manga_root.iterdir() if p.is_dir())


def resolve_pages_dir(root: Path, slug: str | None) -> Path:
    projects = manga_projects(root)
    if slug:
        chosen = root / "docs" / "explainer-src" / "manga" / slug
        if not chosen.is_dir():
            names = ", ".join(p.name for p in projects) or "(none found)"
            sys.exit(f"No manga project '{slug}'. Available: {names}")
        return chosen
    if len(projects) == 1:
        return projects[0]
    if not projects:
        sys.exit(f"No manga projects under {root / 'docs' / 'explainer-src' / 'manga'}.")
    names = ", ".join(p.name for p in projects)
    sys.exit(f"Multiple manga projects found ({names}). Pick one with --slug <name>.")


def load_dotenv(root: Path) -> None:
    """Load root/.env.local then root/.env into os.environ (without overriding
    anything already set), and normalize a fal key alias into FAL_KEY."""
    for fname in (".env.local", ".env"):
        path = root / fname
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    if not os.environ.get("FAL_KEY"):
        for alias in FAL_KEY_ALIASES:
            if os.environ.get(alias):
                os.environ["FAL_KEY"] = os.environ[alias]
                break


def extract_prompt(md_path: Path) -> str:
    """Return everything after the   'Image Prompt:' marker in a page file."""
    text = md_path.read_text(encoding="utf-8")
    idx = text.find(PROMPT_MARKER)
    if idx == -1:
        raise ValueError(f"No '{PROMPT_MARKER}' marker found in {md_path.name}")
    return text[idx + len(PROMPT_MARKER):].strip()


def page_files(pages_dir: Path) -> list[tuple[int, Path]]:
    """Return (page_number, path) for every page-0N.md, sorted."""
    out = []
    for p in sorted(pages_dir.glob("page-*.md")):
        try:
            n = int(p.stem.split("-")[1])
        except (IndexError, ValueError):
            continue
        out.append((n, p))
    return out


def coerce(val: str):
    """Turn a CLI string into int/float/bool where it obviously is one."""
    low = val.lower()
    if low in ("true", "false"):
        return low == "true"
    for cast in (int, float):
        try:
            return cast(val)
        except ValueError:
            pass
    return val


def build_arguments(model: str, prompt: str, opts: dict, extra: dict) -> dict:
    """Per-model argument shape. fal endpoints differ; --arg overrides win."""
    args = {
        "prompt": prompt,
        "num_images": 1,
        "image_size": opts["image_size"],
        "output_format": "png",
    }
    if model.startswith("openai/"):
        # GPT-Image-2 exposes a discrete quality tier.
        args["quality"] = opts["quality"]
    args.update(extra)  # explicit --arg overrides anything above
    return args


def image_url_from_result(result: dict) -> str:
    """Pull the first image URL out of a fal result (handles common shapes)."""
    if isinstance(result.get("images"), list) and result["images"]:
        first = result["images"][0]
        return first["url"] if isinstance(first, dict) else first
    if isinstance(result.get("image"), dict):
        return result["image"]["url"]
    raise ValueError(f"Could not find an image URL in result: {result!r}")


def generate_one(n: int, md_path: Path, model: str, opts: dict, extra: dict, out_dir: Path) -> tuple[int, Path]:
    import fal_client
    import requests

    prompt = extract_prompt(md_path)
    arguments = build_arguments(model, prompt, opts, extra)
    result = fal_client.subscribe(model, arguments=arguments)
    url = image_url_from_result(result)
    out_path = out_dir / f"page-{n}.png"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return n, out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", help="manga project under docs/explainer-src/manga/ (auto if only one)")
    ap.add_argument("--page", type=int, help="generate only this page number")
    ap.add_argument("--force", action="store_true", help="overwrite existing PNGs")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="fal.ai endpoint slug (see --list-models)")
    ap.add_argument("--list-models", action="store_true", help="print curated model suggestions and exit")
    ap.add_argument(
        "--image-size",
        default="portrait_4_3",
        help="square_hd|square|portrait_4_3|portrait_16_9|landscape_4_3|landscape_16_9|auto (default: portrait_4_3 — comic pages are portrait)",
    )
    ap.add_argument(
        "--quality",
        default="high",
        choices=["auto", "low", "medium", "high"],
        help="GPT-Image-2 quality tier (default: high; ignored by non-openai models)",
    )
    ap.add_argument(
        "--arg",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="extra model-specific argument, repeatable (e.g. --arg guidance_scale=3.5)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        help="output dir for page-N.png (default: <repo>/docs/panels — feeds the site)",
    )
    args = ap.parse_args()

    if args.list_models:
        print("Curated fal.ai text-to-image endpoints (pass with --model):\n")
        for slug, blurb in SUGGESTED_MODELS.items():
            print(f"  {slug}\n      {blurb}")
        print("\nAny valid fal.ai endpoint slug works. Default:", DEFAULT_MODEL)
        return 0

    extra = {}
    for item in args.arg:
        if "=" not in item:
            sys.exit(f"--arg must be KEY=VALUE, got: {item!r}")
        key, _, val = item.partition("=")
        extra[key.strip()] = coerce(val.strip())

    root = resolve_root()
    pages_dir = resolve_pages_dir(root, args.slug)
    out_dir = args.out_dir or (root / "docs" / "panels")
    opts = {"image_size": args.image_size, "quality": args.quality}

    load_dotenv(root)
    if not os.environ.get("FAL_KEY"):
        sys.exit(
            "No fal.ai key found. Set FAL_KEY/FAL_API_KEY in the environment "
            f"or in {root / '.env.local'} (FAL_API_KEY=...)."
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    targets = []
    for n, md_path in page_files(pages_dir):
        if args.page and n != args.page:
            continue
        out_path = out_dir / f"page-{n}.png"
        if out_path.exists() and not args.force:
            print(f"page-{n}: exists, skipping (use --force to regenerate)")
            continue
        targets.append((n, md_path))

    if not targets:
        print("Nothing to generate.")
        return 0

    print(f"Generating {len(targets)} panel(s) from {pages_dir.name} with {args.model} "
          f"({opts['image_size']}) -> {out_dir} ...")
    failures = 0
    with ThreadPoolExecutor(max_workers=min(6, len(targets))) as pool:
        futures = {
            pool.submit(generate_one, n, p, args.model, opts, extra, out_dir): n
            for n, p in targets
        }
        for fut in as_completed(futures):
            n = futures[fut]
            try:
                n, out_path = fut.result()
                try:
                    shown = out_path.relative_to(root)
                except ValueError:
                    shown = out_path
                print(f"page-{n}: saved -> {shown}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"page-{n}: FAILED -- {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
