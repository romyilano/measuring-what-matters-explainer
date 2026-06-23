# Spike — Construct Validity in Everyday Vibe Coding

> **What this is:** an exploratory note for the Frontier Tower AI Paper Reading Club.
> It takes the eight failure patterns from *Measuring What Matters: Construct Validity
> in Large Language Model Benchmarks* (arXiv:2511.04703) and asks a smaller, closer
> question: **when we vibe-code with an LLM, what number are we actually trusting, and
> does it touch the thing we care about?**
>
> Status: draft / discussion seed. Not a conclusion.

---

## The one-sentence version of the paper

A benchmark gives you a confident number. **Construct validity** is whether that number
actually measures the abstract thing it claims to ("safety", "reasoning", "coding
ability") — whether the ruler is touching the object. The review of 445 benchmarks found
that, very often, it isn't.

## Why this matters for vibe coding specifically

Vibe coding is a tight loop of *measure → trust → ship*:

- We pick a model partly because a leaderboard said it's "best at code."
- We accept a generated change because the tests went green / the diff looked right /
  it ran once.
- We tell ourselves "it works" and move on.

Every one of those is a **measurement**. And the paper's whole argument is that the gap
between *the number* and *the thing* is where validity quietly dies. So the spike's bet
is: **the same failure modes the paper found in academic benchmarks show up, in miniature,
in our own daily loop — and they're easier to see in our own work than in someone's
arXiv table.**

---

## The eight failures → what they look like at the keyboard

The paper's eight recommendations are stated as things benchmarks *should* do. Flip each
one and you get a failure mode. Here's each, paired with the everyday vibe-coding version.

| # | Paper's recommendation | The failure when ignored | The vibe-coding version (obvious in daily practice) |
|---|------------------------|---------------------------|------------------------------------------------------|
| 1 | **Define the phenomenon** | ~48% of definitions are *contested* | We ask the model to make code "clean" / "robust" / "production-ready" — words we never defined. We grade the output against a target that doesn't exist. |
| 2 | **Measure only the phenomenon** | 61% bundle many abilities into one score | "It can build the app" actually bundles: reads the prompt, knows the framework, writes correct logic, formats output. When it fails we can't tell *which* broke. |
| 3 | **Construct representative datasets** | 40.7% use constructed (not real-world) tasks | We judge a model on a toy todo-app or a single happy-path prompt, then deploy it against our messy real repo. The demo task ≠ the job. |
| 4 | **Acknowledge dataset-reuse limits** | 42.6% reuse data without checking fit | We reuse the same few "does it know X?" prompts to vet every new model, never asking if those prompts still represent what we actually do now. |
| 5 | **Prepare for contamination** | only some test for leakage | The model aces a well-known algorithm/LeetCode-style task — because it memorized it, not because it reasoned. Green checkmark, zero signal. The classic "it nails the textbook problem, fumbles our weird internal API." |
| 6 | **Use statistical methods** | only ~16% report any uncertainty | We run the prompt **once**. It worked once → "it works." No notion that the *next* run, with temperature > 0, might not. We report a point estimate from n=1. |
| 7 | **Conduct error analysis** | most don't examine *how* it fails | When generated code fails we re-prompt ("try again") instead of looking at the failure mode. We treat the red as noise, not data. |
| 8 | **Justify construct validity** | 53.4% never justify the number | "Tests pass" → "the feature works." We never argue *why* a passing test should imply the behavior we actually want. The number is taken as self-evidently meaningful. |

The point of the table isn't rigor — it's recognition. Most readers will see at least three
rows they did *this week*.

---

## The sharpest analogy: the green test suite is an exact-match grader

The paper's most damning single statistic is that **81.3% of benchmarks rely on
exact-match scoring** — string-equals against a reference answer, which over- and
under-counts in obvious ways (a correct answer phrased differently scores zero; a
plausible-but-wrong answer that happens to match scores one).

The everyday twin: **a passing test suite is exact-match scoring for "the code works."**

- It rewards matching the assertions you happened to write, not the behavior you wanted.
- A change that's correct but breaks a brittle test scores "fail."
- A change that's wrong in a way no test covers scores "pass."
- Green is treated as the construct ("it works") when it's only ever the proxy
  ("these specific assertions held this once").

This is the cleanest bridge from the paper to the room: *we already know not to fully
trust a green checkmark — the paper just gives us the vocabulary for **why** the
checkmark and the truth can diverge.*

---

## What would change if we took construct validity seriously in our loop

Not a prescription — a provocation for discussion:

- Before accepting "it works," name the **phenomenon** (#1): what behavior, on what
  inputs, would actually count as working?
- Run it **more than once** (#6) when the output is stochastic; notice the variance
  instead of hiding it.
- When it fails, **read the failure** (#7) before re-rolling the dice.
- Distrust the **memorized win** (#5): test on something the model can't have seen.
- Separate the **bundled abilities** (#2): is the failure in understanding, knowledge,
  or execution?

---

## Topics of discussion

1. **What's *your* exact-match grader?** Everyone name the one green checkmark they trust
   more than it deserves (CI passing? type-checks? "it ran"? a clean-looking diff?).
2. **The contested-definition problem (#1):** when we tell an LLM to write "clean" or
   "idiomatic" or "secure" code — whose definition is it using, and how would we even
   know if it picked a different one than us?
3. **n=1 culture (#6):** we almost never run a generation twice. Is single-shot
   acceptance a reasonable engineering tradeoff, or are we just reporting a point
   estimate with no error bar — exactly what the paper criticizes?
4. **Contamination at the keyboard (#5):** how much of a model's apparent coding skill is
   reasoning vs. memorized public code? Does that distinction matter for our work, or
   only for benchmarks?
5. **Leaderboard → model choice:** we pick coding models off aggregate scores
   (SWE-bench, etc.). Given the paper, how much should those numbers move our decision —
   and what would a *construct-valid* "is this model good at MY codebase" test look like?
6. **Who pays for invalidity?** In a benchmark, an invalid score misleads a reader. In
   vibe coding, who eats the cost when "it works" was hollow — and how far downstream does
   it surface?
7. **Is "vibes" actually the honest answer?** The paper's payoff is that an honest score
   is *smaller* but means something. Is trusting human judgment ("it feels right after I
   read it") a more construct-valid measure than any automated proxy we have?
8. **The eight recommendations as a code-review checklist:** could we adapt them into a
   short pre-merge ritual for AI-generated changes? Which of the eight are realistic to
   actually do, and which are aspirational?

---

## How could we test this in the real world?

Concrete, low-cost experiments we could run as a group (or individually before next
session) to *see* construct-validity failures in our own loop rather than take the paper's
word for it.

### Experiment A — The n=1 fallacy (recommendation #6)
Take one non-trivial prompt. Run it **10 times** at the same settings (temperature > 0).
Count how many distinct outputs you get and how many actually pass your own definition of
"correct." Report it as `passed/10`, not "it works." Predict before running; compare.
*Hypothesis: variance is higher than anyone guessed, and our usual single run is a lucky
draw as often as not.*

### Experiment B — Contamination probe (recommendation #5)
Give the model (1) a famous, well-documented problem and (2) a structurally identical
problem dressed in your weird internal domain / a renamed API. Compare success rates. A
big gap is the memorization tell. *Cheap, and very legible in a live demo.*

### Experiment C — The exact-match audit (recommendation #8, the 81% stat)
Take a real PR where "the tests passed." Manually ask: for each behavior you actually
care about, is there an assertion that would *fail* if that behavior broke? Tally
behaviors-cared-about vs. behaviors-actually-tested. The ratio is your local construct
validity. *Hypothesis: green covers far less of "it works" than it feels like it does.*

### Experiment D — Contested definitions (recommendation #1)
Ask 3–4 people to independently write down what "clean code" / "production-ready" means in
one sentence *before* the session. Compare. Then ask a model the same. *Hypothesis: we
don't agree with each other, so "make it clean" was never a measurable instruction —
~48%-of-definitions-contested, reproduced live in the room.*

### Experiment E — Bundled abilities (recommendation #2)
On a task the model fails, decompose: did it (a) misread the requirement, (b) lack the
API/framework knowledge, or (c) reason/execute wrong with correct understanding? Track
which bucket failures fall into across several tasks. *Hypothesis: "bad at coding" is
really one specific sub-ability failing repeatedly, and the aggregate score hid it.*

### Experiment F — Error analysis vs. re-roll (recommendation #7)
For one work session, every time generated code fails, **write one sentence** about the
failure mode before re-prompting. At the end, cluster the sentences. *Hypothesis: a small
number of recurring failure modes account for most re-rolls — and naming them would have
been faster than blind retries.*

### A possible group deliverable
Each of A–F produces a single number or short list. Collected, they're a tiny
**construct-validity report card for our own vibe-coding practice** — the paper's method
(systematic review → percentages → recommendations) turned on ourselves at n=1-room scale.
Deliberately small, deliberately honest. Which is the paper's whole point.

---

## Open questions / where this spike is thin

- This maps benchmark validity onto *individual* practice. The paper is about *systemic*
  measurement across a field — is the analogy load-bearing, or does it break when we go
  from "the field's knowledge" to "did my feature ship"?
- Construct validity comes from psychometrics (measuring latent human traits). LLM
  benchmarks borrowed it; we're borrowing it again. Each hop may lose something — worth
  naming what.
- "Vibes" might genuinely be more valid than our proxies *and* unscalable. The interesting
  tension is whether construct validity and automation are at odds in our daily work.

---

*Source: Bean et al. (Andrew M. Bean, Ryan Othniel Kearns, Angelika Romanou, et al.; 42
authors), "Measuring what Matters: Construct Validity in Large Language Model Benchmarks,"
arXiv:2511.04703; accepted to NeurIPS 2025 (Datasets & Benchmarks Track). Companion
explainer: `docs/index.html` /
`docs/explainer-src/`. Stats quoted here are from `docs/explainer-src/manga/construct-validity/notes.md`.*
