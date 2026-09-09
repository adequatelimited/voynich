# H004: local preceding-context near-edit screen

Status: **static matched-null gate passed; copy/edit mechanism remains unvalidated**

## Claim boundary

H004-v1 asks only whether the preceding local prose context predicts the
transcriptional form of the next certain basic-EVA token beyond a matched
static page-frequency and layout baseline. It assigns no sound, word class,
meaning, or translation. A positive result is compatible with copying, a
Markov process, morphology, syntax, topic sequence, scribal convention, or a
transcription artifact.

## Frozen protocol

- Input: byte-pinned `data/raw/transcriptions/ZL3b-n.txt`.
- Include only `P*` loci with valid locators and known illustration `$I`,
  Currier `$L`, and hand `$H` values.
- Use only certain basic-EVA components. An excluded or uncertain component,
  paragraph boundary, or I/L/H change resets the causal sequence.
- A target requires the ten immediately preceding eligible tokens in the same
  sequence. Pages require at least ten targets.
- Compare EVA code-point strings with Levenshtein distance. This is not a claim
  that an EVA code point is a manuscript glyph.
- Co-primary metrics are the page rate with minimum predecessor distance at
  most one, and the page rate with minimum distance exactly one. Exact repeats
  are a diagnostic only.
- Split whole pages with `SHA256("H004-v1:" + page_id)`; first byte below 51 is
  reserved. The split was frozen before H004 effect inspection, but the
  manuscript and transcription are not pristine, never-inspected material.
- For each of 9,999 permutations with seed 4004, shuffle token identities only
  within page × I × L × H × EVA length × paragraph-initial status × line
  position (`singleton`, `first`, `middle`, `last`) cells. Recompute causal
  scores. This preserves the exact page token multiset and the named layout
  variables while destroying local order.
- Compute each rate within page and average pages equally. Use one-sided Monte
  Carlo `p = (1 + count(null >= observed)) / (permutations + 1)`.

## Frozen advancement gate

The static predictive-order screen advances only if all conditions hold:

1. At least 30 reserved pages and 1,500 targets; Currier A and B each have at
   least five pages and 200 targets; at least 80% of targets are in movable
   permutation cells.
2. Both co-primary metrics have absolute improvement at least 0.02,
   `p <= 0.005`, and positive page residuals on more than 60% of pages.
3. Both metrics have positive improvement and `p <= 0.025` separately in
   Currier A and B.

Passing this gate does **not** advance a copy/edit generator. Parisel's
word-level Markov simulations show that surface sequential statistics can
reproduce a directional Voynich signature without identifying a generator:
<https://arxiv.org/html/2604.19762v2#S3.SS4>. Before a mechanism claim, this
project requires discovery-trained order-1/order-2 Markov surrogates and an
cross-transcription STA-family robustness check. Neither is implemented in
H004-v1.

## Result

The reserved partition contained 33 eligible pages and 2,072 targets; 2,000
targets (96.53%) belonged to cells containing more than one distinct token
type and therefore capable of changing the target identity. Both Currier strata
met the frozen breadth minimums: A contributed 458 targets on 16 pages and B
contributed 1,614 targets on 17 pages.

Against 9,999 matched permutations:

- exact-or-one-edit rate was 0.3062 versus a 0.2558 null mean
  (`delta = +0.0504`, one-sided Monte Carlo `p = 0.0001`, positive residual on
  26 of 33 pages);
- one-edit-without-exact rate was 0.2281 versus 0.1902
  (`delta = +0.0379`, `p = 0.0003`, positive residual on 25 of 33 pages);
- the exact-repeat diagnostic was 0.0781 versus 0.0656
  (`delta = +0.0125`, `p = 0.0326`).

Both co-primary metrics also met the frozen Currier A/B robustness checks. The
static predictive-order gate therefore passed. This establishes a local order
effect in the pinned transcription relative to the named static null. It does
not distinguish a copying/editing process from ordinary word-level sequential
dependence, morphology, syntax, topic continuity, scribal practice, or a
transcription effect. No token receives a gloss.

Machine-readable and rendered results are in
`results/h004-local-order.json` and `results/h004-local-order.md`.

Rebuild command:

```sh
python3 scripts/analyze_local_order.py
```
