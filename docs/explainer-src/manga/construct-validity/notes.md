# Notes — construct-validity

## Source
*Measuring what Matters: Construct Validity in Large Language Model Benchmarks*,
arXiv:2511.04703. A systematic review by 29 expert reviewers of 445 LLM benchmarks
from leading NLP/ML venues, diagnosing construct-validity failures and offering eight
recommendations.

## Key figures used (kept faithful, rounded for captions)
- 445 benchmarks reviewed; 29 expert reviewers.
- ~47.8% of phenomenon definitions are *contested* → "~48% of definitions contested" (pages 4).
- 61.2% treat the phenomenon as a composite but don't measure sub-parts separately → page 2/4 "more than one thing in the crate."
- 40.7% use constructed (not real-world) tasks; 27% convenience sampling; 42.6% reuse data without checking representativeness → page 3 "stand-in" / page 5 cards 3–4.
- 81.3% rely on exact-match scoring → "81%" (pages 3–4).
- Only ~16% use any statistical testing / uncertainty → "16% report uncertainty" (page 4) and the error-band gauge (pages 5–6).
- 53.4% give no explicit validity justification → "half never justified the number" (page 4); recommendation 8 (page 5).

## The eight recommendations (paper → index cards on page 5)
1. Define the phenomenon (precise, operational definition).
2. Measure only the phenomenon (control confounding abilities).
3. Construct representative datasets (sample the real task space).
4. Acknowledge dataset-reuse limitations (document strengths/weaknesses).
5. Prepare for contamination (test for and detect leakage).
6. Use statistical methods (report uncertainty for all primary scores).
7. Conduct error analysis (qualitative + quantitative failure modes).
8. Justify construct validity (tie the benchmark to real-world relevance).

## Metaphor decisions
- Benchmark → lobby weighing scale; keeps the "one confident number" feel and lets page 6 mirror page 1.
- Phenomenon → sealed stenciled crate; "safety/robustness" as a word nobody opened.
- Construct validity → steel tape measure literally touching (or not touching) the thing.
- Exact-match → bubble-sheet grader; contamination → answer key left in the room; uncertainty → gauge needle with/without an error band.
- Eight recommendations → eight plain index cards, deliberately un-flashy.

## Omitted / could expand in a sequel
- The reviewer methodology and inter-rater process (how 29 people agree).
- The taxonomy detail behind each percentage.
- Specific named benchmarks (kept generic on purpose — the paper's point is systemic, not a callout).
- A page on *measurement theory* lineage (construct validity from psychometrics).

## Assumptions
- Exact percentages are presented rounded and as captions, not on-panel charts, to stay in the deadpan register.
- The "61.0 ± 3.4" honest readout on page 6 is illustrative, not a figure from the paper.
