# Clean re-run of the generative-falsification pilots — pre-registered protocol

**Status:** written and committed BEFORE the script was run. Rules are frozen; the report
applies them mechanically and records any deviation.

**Why.** The adversarial critique (`experiments/adversarial-critique/`) showed that every
pilot (M2 self-citation, M3 entry doodler, M4 Stolfi template, M5/M5b grille) was fitted
to a corpus parse that contained 2,454 artefact types, that the "best" configuration of
each model was selected on the same metrics it was then reported as matching, and that
the habit tables were built from the whole corpus that was then scored. This re-run fixes
all three at once.

## Design

**Corpus.** `data/corpora/ZL3b-n.txt`, parsed with the critique's clean parser
(`adversarial_critique.clean_load`). Two treatments of IVTFF uncertain spaces (`,`):
**S** = space (primary), **M** = merged (the pilots' choice). Both are reported in full.

**Held-out split.** Pages in file order are assigned alternately to FIT (even index) and
TEST (odd index). This balances Currier language and section across halves and keeps
every page's neighbours in the other half. All page-level metrics on a half are computed
on that half's page sequence (so "adjacent" means adjacent within the half); real and
generated data are measured identically.

**Habit tables from FIT only.** M2's character-bigram habit model, M3/M4's corpus word
pool and Stolfi layer weights, and M5/M5b's fragment table and row list are built from the
FIT half's words only. The generators produce a full 226-page corpus (page sizes from the
real pages) so that carry-over between consecutive pages is preserved; scoring then uses
the TEST pages only.

**Model selection.** Each model's grid is the family's own grid, unchanged:
M2 27 configs, M3 24, M4 12, M5 12 (+ M5b 16). Selection minimises the family's composite
distance (sum of squared relative errors over the family's nine keys: ttr, H1, H2|1, Zipf,
word length, final-char H, adjacent J, distant J, page-unique share) computed on the **FIT**
half against the real FIT half. The selected configuration is then scored on the **TEST**
half against the real TEST half. Seed 408 (the family's).

**Metrics.** The family's formulas, unchanged, plus hapax share of types and first-char H.

## Decision rules (frozen)

- **R5.1 Per-metric match on TEST.** A metric is matched if the selected model's TEST value
  is within tolerance of the real TEST value: ttr ± 0.02; H2|1 ± 0.15 bits; final-char H
  ± 0.15 bits; Zipf ± 0.10; word length ± 0.3; adjacent J ± 0.015; distant J ± 0.015;
  page-unique share ± 0.03; hapax share ± 0.03. The count of matched metrics out of nine is
  the model's held-out score. (Tolerances were chosen before the run as roughly twice the
  multi-seed SD the family reported, 0.02 on entropies.)
- **R5.2 Residue restated.** The family's residue claim ("H2|1, final-char H and Zipf are
  unmatched; page structure and word length are matched") is re-evaluated from the R5.1
  table of the best model under treatment S. Each of the five named metrics is labelled
  MATCHED or UNMATCHED on held-out data.
- **R5.3 Selection optimism.** For each model, if the composite distance on TEST exceeds
  the distance on FIT by more than 25 %, the model is labelled **OVERFIT** (its earlier
  in-sample "match" was selection optimism). Otherwise **GENERALISES**.
- **R5.4 Ranking.** Whether the family's ranking (M5b < M5 < M4 < M3 < M2 in distance) holds
  on TEST is reported; no gate.

## A2′ — cipher advocate with corrected gates

Same untuned construction as the critique (frequency-rank assignment from the clean FIT
half), plaintexts Latin Vulgate (35k tokens) and Culpeper entries (≤ 35k tokens). Cipher
grid fixed here, all reported, 12 trials disclosed: abbreviation ∈ {none, drop non-initial
vowels} × homophones per letter k ∈ {1, 2, 3}; homophone choice weighted by n-gram
frequency, seed 408.

- **R6.1** A cipher **reproduces the residue** if, against the clean manuscript under the
  same treatment (S or M, both tried), it satisfies all five: ttr within ± 0.03; H2|1 ≤
  manuscript + 0.20; final-char H ≤ manuscript + 0.20; word length within ± 1.0; Zipf within
  ± 0.15. Any hit → **RESIDUE NON-DISCRIMINATING (device vs cipher)**. No hit → **NOT
  REPRODUCED BY 12 UNTUNED CIPHERS** (weak, by design).

## Not in this protocol

No new generator, no new metric family, no probability judgments. Section-by-section
analysis remains exploratory and separate.

## Reproduction

```
python clean_rerun.py --repo ../.. --lab <dir with bibles/ and pg49513.txt> --out results/
```

Stdlib only; deterministic; uses `critique_lib.py` (a verbatim copy of the critique's parser and metric code,
`experiments/adversarial-critique/adversarial_critique.py` in PR #10, so that this branch
is self-contained) and the family's generators, vendored unchanged in
`family_generators.py` with per-function provenance comments.
