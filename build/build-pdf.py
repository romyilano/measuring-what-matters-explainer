#!/usr/bin/env python3
"""Build docs/construct-validity.pdf — the downloadable comic.

Structure:
  1. Cover page reproducing the website masthead (title, standfirst, credit).
  2. The six comic panels, one per page (docs/panels/page-1..6.png).
  3. Two recall worksheets — a "whiteboard" page (sketch what you remember from
     memory) and a "discussion & avenues" mind-map page (fill in by hand).
  4. A divider page, then the full arXiv paper (2511.04703) appended at the back.

The cover + comic pages are rendered with headless Chrome (for real
typography), then merged with the arXiv PDF using pypdf.

Usage:
    pip install pypdf            # plus a local Google Chrome
    python build/build-pdf.py                 # downloads the paper itself
    python build/build-pdf.py --paper some.pdf  # use a local paper PDF
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from pypdf import PdfWriter, PdfReader

ARXIV_ID = "2511.04703"
ARXIV_PDF_URL = f"https://arxiv.org/pdf/{ARXIV_ID}"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def find_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / "docs" / "index.html").is_file():
            return d
    return start.parent


ROOT = find_root(Path(__file__).resolve().parent)
PANELS = ROOT / "docs" / "panels"
OUT_PDF = ROOT / "docs" / "construct-validity.pdf"


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
    sys.exit("Could not find Google Chrome/Chromium. Set one in CHROME_CANDIDATES.")


def cover_and_comic_html() -> str:
    """The cover (masthead) + one full page per comic panel."""
    pages = "".join(
        f'<section class="plate"><img src="{(PANELS / f"page-{n}.png").as_uri()}"></section>'
        for n in range(1, 7)
    )
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;1,9..144,400&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500&display=swap" rel="stylesheet">
<style>
  :root {{ --paper:#e6e9e4; --ink:#1d2128; --muted:#6c7178; --spot:#3c5d72; --line:#1d2128; }}
  @page {{ size: 8.5in 11in; margin: 0; }}
  * {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ background: var(--paper); color: var(--ink); font-family: "Newsreader", Georgia, serif; }}
  a {{ color: var(--spot); text-decoration: none; }}
  section {{ width: 8.5in; height: 11in; overflow: hidden; }}
  section + section {{ page-break-before: always; }}
  .cover {{ padding: 1.1in 1.05in; display: flex; flex-direction: column; justify-content: center; }}
  .kicker {{ text-transform: uppercase; letter-spacing: 0.3em; font-size: 0.8rem; font-weight: 600;
             color: var(--spot); margin: 0 0 30px; }}
  .cover h1 {{ font-family: "Fraunces", serif; font-weight: 500; font-size: 4.6rem; line-height: 0.98;
               letter-spacing: -0.025em; margin: 0; }}
  .cover h1 em {{ font-style: italic; color: var(--spot); }}
  .standfirst {{ font-family: "Fraunces", serif; font-size: 1.7rem; color: var(--muted); font-style: italic;
                 line-height: 1.3; max-width: 22em; margin: 34px 0 0; }}
  .byline {{ font-size: 0.74rem; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted);
             margin-top: 40px; border-top: 1.5px solid var(--line); padding-top: 14px;
             display: flex; gap: 28px; flex-wrap: wrap; }}
  .credit {{ font-size: 0.74rem; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted);
             margin: 14px 0 0; }}
  .plate {{ display: flex; align-items: center; justify-content: center; padding: 0.5in; }}
  .plate img {{ max-width: 7.5in; max-height: 10in; width: auto; height: auto; object-fit: contain;
                border: 1.5px solid var(--line); box-shadow: 8px 8px 0 rgba(29,33,40,0.10); }}
  .divider {{ padding: 1.3in 1.05in; display: flex; flex-direction: column; justify-content: center; }}
  .divider h2 {{ font-family: "Fraunces", serif; font-weight: 500; font-size: 3.2rem; margin: 0;
                 letter-spacing: -0.02em; }}
  .divider p {{ font-size: 1.1rem; color: var(--muted); max-width: 26em; line-height: 1.5; margin: 24px 0 0; }}
  .worksheet {{ padding: 0.85in 1.05in 0.75in; display: flex; flex-direction: column; }}
  .worksheet .kicker {{ margin: 0 0 16px; }}
  .worksheet h2 {{ font-family: "Fraunces", serif; font-weight: 500; font-size: 2.9rem;
                   letter-spacing: -0.02em; margin: 0; line-height: 1.0; }}
  .worksheet h2 em {{ font-style: italic; color: var(--spot); }}
  .ws-lede {{ font-family: "Fraunces", serif; font-size: 1.22rem; font-style: italic; color: var(--muted);
              line-height: 1.4; max-width: 30em; margin: 16px 0 20px; }}
  .ws-board {{ flex: 1; border: 1.6px solid var(--line); border-radius: 3px; position: relative;
               box-shadow: 8px 8px 0 rgba(29,33,40,0.08);
               background-image: radial-gradient(rgba(29,33,40,0.12) 1.1px, transparent 1.1px);
               background-size: 24px 24px; background-position: 14px 14px; }}
  .ws-hint {{ position: absolute; bottom: 12px; right: 16px; font-size: 0.7rem; letter-spacing: 0.2em;
              text-transform: uppercase; color: var(--muted); }}
  .ws-foot {{ font-size: 0.82rem; color: var(--muted); margin: 14px 0 0; font-style: italic; }}
  .ws-grid {{ flex: 1; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 16px; }}
  .ws-cell {{ border: 1.4px solid var(--line); border-radius: 3px; padding: 14px 16px 16px;
              display: flex; flex-direction: column;
              background-image: radial-gradient(rgba(29,33,40,0.09) 1px, transparent 1px);
              background-size: 22px 22px; background-position: 11px 44px; }}
  .ws-cell .num {{ font-size: 0.7rem; letter-spacing: 0.2em; text-transform: uppercase;
                   color: var(--spot); margin: 0 0 5px; }}
  .ws-cell h3 {{ font-family: "Fraunces", serif; font-weight: 500; font-size: 1.12rem; margin: 0;
                 color: var(--ink); line-height: 1.15; }}
</style></head><body>
  <section class="cover">
    <p class="kicker">An Explainer, in Six Pages</p>
    <h1>Measuring <em>What Matters</em></h1>
    <p class="standfirst">A confident benchmark score can measure almost nothing. Twenty-nine reviewers read four hundred and forty-five of them to prove it.</p>
    <div class="byline"><span>After arXiv:{ARXIV_ID}</span><span>Featuring Dana &amp; Theo</span></div>
    <p class="credit">Made by <a href="https://www.romyilano.com">romy</a> to study whitepapers at <a href="https://frontiertower.io">Frontier Tower</a>. <a href="https://luma.com/frontier-tower-ai-paper-reading-club-wee-d4d5?tk=dDff6R">AI Paper Reading Club</a> &middot; June 23, 2026.</p>
  </section>
  {pages}
  <section class="worksheet">
    <p class="kicker">Worksheet · One of Two</p>
    <h2>From memory, <em>the whiteboard</em></h2>
    <p class="ws-lede">Close the comic — don't peek. Sketch out what you recollect and understand,
       as if you were standing at a whiteboard explaining it to a colleague. Boxes, arrows, a few words.</p>
    <div class="ws-board"><span class="ws-hint">your whiteboard</span></div>
    <p class="ws-foot">Whatever stays blank is the part worth re-reading. Recall first, re-read second.</p>
  </section>
  <section class="worksheet">
    <p class="kicker">Worksheet · Two of Two</p>
    <h2>Discussion &amp; <em>avenues</em></h2>
    <p class="ws-lede">Mind-map this by hand — on your tablet if you have one, or a physical whiteboard.
       The questions matter more than the answers: what did you actually learn, and where would you take it next?</p>
    <div class="ws-grid">
      <div class="ws-cell"><p class="num">01</p><h3>What did I actually learn?</h3></div>
      <div class="ws-cell"><p class="num">02</p><h3>What's still fuzzy?</h3></div>
      <div class="ws-cell"><p class="num">03</p><h3>Avenues to explore next</h3></div>
      <div class="ws-cell"><p class="num">04</p><h3>Who would I ask? What would I test?</h3></div>
    </div>
  </section>
  <section class="divider">
    <h2>The paper, in full</h2>
    <p>What follows is the complete source paper this comic explains —
       <em>Measuring What Matters: Construct Validity in Large Language Model Benchmarks</em>,
       arXiv:{ARXIV_ID}.</p>
  </section>
</body></html>"""


def render_front_pdf(chrome: str, work: Path) -> Path:
    html_path = work / "front.html"
    html_path.write_text(cover_and_comic_html(), encoding="utf-8")
    front_pdf = work / "front.pdf"
    subprocess.run(
        [
            chrome, "--headless=new", "--disable-gpu",
            # Isolated profile so we never attach to a Chrome the user already has
            # open (which makes --print-to-pdf inherit its page setup and mangle
            # pagination).
            f"--user-data-dir={work / 'chrome-profile'}",
            "--no-pdf-header-footer", "--allow-file-access-from-files",
            "--virtual-time-budget=15000",
            f"--print-to-pdf={front_pdf}", html_path.as_uri(),
        ],
        check=True, capture_output=True,
    )
    if not front_pdf.exists():
        sys.exit("Chrome did not produce the front PDF.")
    return front_pdf


def get_paper_pdf(work: Path, supplied: str | None) -> Path:
    if supplied:
        return Path(supplied)
    dest = work / "paper.pdf"
    req = urllib.request.Request(
        ARXIV_PDF_URL, headers={"User-Agent": "paper-reading-club/1.0 (research)"}
    )
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--paper", help="path to a local arXiv paper PDF (else downloaded)")
    args = ap.parse_args()

    chrome = find_chrome()
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        front_pdf = render_front_pdf(chrome, work)
        paper_pdf = get_paper_pdf(work, args.paper)

        writer = PdfWriter()
        for reader in (PdfReader(str(front_pdf)), PdfReader(str(paper_pdf))):
            for page in reader.pages:
                writer.add_page(page)
        with open(OUT_PDF, "wb") as f:
            writer.write(f)

    n = len(PdfReader(str(OUT_PDF)).pages)
    print(f"Wrote {OUT_PDF.relative_to(ROOT)} ({n} pages).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
