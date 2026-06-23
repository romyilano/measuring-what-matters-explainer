# Measuring What Matters — an educational comic

A six-page deadpan comic explaining **construct validity in LLM benchmarks**, after
the paper *Measuring what Matters: Construct Validity in Large Language Model Benchmarks*
(arXiv:2511.04703).

**The idea in one line:** a benchmark score is only as good as whether the test actually
measures the thing it claims to. A team of 29 reviewers read 445 benchmarks and found that
most don't — the definition is contested, the task is a stand-in, and the score is a blunt
exact-match with no error bars. The paper gives eight fixes.

## Cast
- **Dana** — an ML researcher who shipped the leaderboard slide and is starting to doubt it.
- **Theo** — a deadpan measurement scientist who keeps asking what is actually being measured.

## The six pages
1. The trusted number — everyone celebrates a "safe" score.
2. Construct validity — does the ruler touch the thing?
3. The systematic review — 445 benchmarks, three places measurement breaks.
4. The hidden numbers — exact-match, no uncertainty, contested definitions, contamination.
5. The eight recommendations — how to measure what matters.
6. The honest score — smaller, with error bars, and finally meaningful.

## Pipeline
Generate each page's image from `page-0N.md` → save to `panels/construct-validity_pageNN.png`
→ (for the explainer site, also copy to `docs/panels/page-N.png`) → optionally bundle a PDF.
Open `index.html` here to copy each prompt without spending API credits.
