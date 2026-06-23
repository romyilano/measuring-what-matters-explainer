#!/usr/bin/env python3
"""Generate the six explainer comic panels via fal.ai (Grok text-to-image).

Each docs/explainer-src/manga/construct-validity/page-0N.md already contains a
fully self-contained image prompt (locked style + recurring cast + panel
script). We extract the prompt body and send one request per page to fal.ai,
saving the result to docs/panels/page-N.png.

Usage:
    export FAL_KEY="<your fal.ai key>"
    pip install fal-client requests
    python scripts/generate-panels.py              # all missing pages
    python scripts/generate-panels.py --force      # regenerate everything
    python scripts/generate-panels.py --page 3     # just page 3
    python scripts/generate-panels.py --model fal-ai/...   # override endpoint
"""

from __future__ import annotations

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import fal_client
import requests

# ---------------------------------------------------------------------------
# Text-to-image endpoint. Override with --model or $FAL_IMAGE_MODEL.
MODEL_ID = os.environ.get("FAL_IMAGE_MODEL", "openai/gpt-image-2")
# ---------------------------------------------------------------------------


def find_root(start: Path) -> Path:
    """Walk up from this file until we find the dir containing docs/explainer-src."""
    for d in [start, *start.parents]:
        if (d / "docs" / "explainer-src").is_dir():
            return d
    return start.parent  # fallback


ROOT = find_root(Path(__file__).resolve().parent)
PAGES_DIR = ROOT / "docs" / "explainer-src" / "manga" / "construct-validity"
DEFAULT_OUT_DIR = PAGES_DIR / "grok"
PROMPT_MARKER = "Image Prompt:"

# fal_client authenticates via the FAL_KEY env var. Accept these aliases too.
FAL_KEY_ALIASES = ("FAL_KEY", "FAL_AI_KEY", "FAL_API_KEY")


def load_dotenv() -> None:
    """Load ROOT/.env.local then ROOT/.env into os.environ (without overriding
    anything already set), and normalize a fal key alias into FAL_KEY."""
    for fname in (".env.local", ".env"):
        path = ROOT / fname
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
    """Return everything after the 'Image Prompt:' marker in a page file."""
    text = md_path.read_text(encoding="utf-8")
    idx = text.find(PROMPT_MARKER)
    if idx == -1:
        raise ValueError(f"No '{PROMPT_MARKER}' marker found in {md_path.name}")
    return text[idx + len(PROMPT_MARKER):].strip()


def page_files() -> list[tuple[int, Path]]:
    """Return (page_number, path) for every page-0N.md, sorted."""
    out = []
    for p in sorted(PAGES_DIR.glob("page-*.md")):
        try:
            n = int(p.stem.split("-")[1])
        except (IndexError, ValueError):
            continue
        out.append((n, p))
    return out


def image_url_from_result(result: dict) -> str:
    """Pull the first image URL out of a fal result (handles common shapes)."""
    if isinstance(result.get("images"), list) and result["images"]:
        first = result["images"][0]
        return first["url"] if isinstance(first, dict) else first
    if isinstance(result.get("image"), dict):
        return result["image"]["url"]
    raise ValueError(f"Could not find an image URL in result: {result!r}")


def generate_one(n: int, md_path: Path, model: str, opts: dict, out_dir: Path) -> tuple[int, Path]:
    prompt = extract_prompt(md_path)
    arguments = {
        "prompt": prompt,
        "image_size": opts["image_size"],
        "quality": opts["quality"],
        "num_images": 1,
        "output_format": "png",
    }
    result = fal_client.subscribe(model, arguments=arguments)
    url = image_url_from_result(result)
    out_path = out_dir / f"page-{n}.png"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return n, out_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=int, help="generate only this page number")
    ap.add_argument("--force", action="store_true", help="overwrite existing PNGs")
    ap.add_argument("--model", default=MODEL_ID, help="fal.ai endpoint slug")
    ap.add_argument(
        "--image-size",
        default="portrait_4_3",
        help="square_hd|square|portrait_4_3|portrait_16_9|landscape_4_3|landscape_16_9|auto (default: portrait_4_3 — comic pages are portrait)",
    )
    ap.add_argument(
        "--quality",
        default="high",
        choices=["auto", "low", "medium", "high"],
        help="GPT-Image-2 quality tier (default: high)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"directory for page-N.png output (default: {DEFAULT_OUT_DIR})",
    )
    args = ap.parse_args()
    opts = {"image_size": args.image_size, "quality": args.quality}
    out_dir = args.out_dir

    load_dotenv()
    if not os.environ.get("FAL_KEY"):
        sys.exit(
            "No fal.ai key found. Set FAL_KEY/FAL_API_KEY in the environment "
            f"or in {ROOT / '.env.local'} (FAL_API_KEY=...)."
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    targets = []
    for n, md_path in page_files():
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

    print(f"Generating {len(targets)} panel(s) with {args.model} "
          f"({opts['image_size']}, quality={opts['quality']}) -> {out_dir} ...")
    failures = 0
    with ThreadPoolExecutor(max_workers=min(6, len(targets))) as pool:
        futures = {pool.submit(generate_one, n, p, args.model, opts, out_dir): n for n, p in targets}
        for fut in as_completed(futures):
            n = futures[fut]
            try:
                n, out_path = fut.result()
                try:
                    shown = out_path.relative_to(ROOT)
                except ValueError:
                    shown = out_path
                print(f"page-{n}: saved -> {shown}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"page-{n}: FAILED -- {exc}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
