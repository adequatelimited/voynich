# Clean re-run of the generative-falsification pilots — results

**Protocol:** [PROTOCOL.md](PROTOCOL.md), committed before the run (commit `8873bfa`).
**Script:** `clean_rerun.py` (imports the critique's parser and metric formulas; the pilots'
generators are vendored unchanged in `family_generators.py`). **Output:** `results/results.json`,
`results/stdout.txt`; exploratory `results/insample_clean.json`.
**Run record:** `experiments/runs/2026-09-07T093000Z-clean-rerun/`.

Three things changed at once relative to PRs #3–#6: the corpus is parsed cleanly (no
mark-up inside words), the habit tables are built from the FIT half only, and each model's
configuration is chosen on the FIT half and scored on the TEST half. The grids, seed and
composite distance are the family's own.

## Verdicts by the frozen rules

| Rule | Result |
|---|---|
| R5.1 held-out matches (of 9), treatment S | M2 **3**, M3 2, M5b 2, M4 1, M5 1 |
| R5.1 held-out matches (of 9), treatment M | M3 **3**, M5b **3**, M2 2, M4 1, M5 1 |
| R5.2 residue on held-out data (best model under S = M2) | H2\|1 **UNMATCHED**, final-char H **UNMATCHED**, Zipf **UNMATCHED**, adjacent J MATCHED, word length UNMATCHED |
| R5.3 selection optimism | all five models GENERALISE (TEST within 25 % of FIT) — but see the note on the split |
| R5.4 ranking on TEST | **M2 < M3 < M5b < M5 < M4** under both treatments. The family's order (M5b best, M2 worst) is reversed |
| R6.1 cipher advocate, corrected gates | **NOT REPRODUCED BY 12 UNTUNED CIPHERS** |

## Held-out results, treatment S (uncertain spaces as spaces)

Real values are the TEST half (113 pages). Models were selected on the other 113 pages.
✓ = within the pre-registered tolerance.

| Metric | real TEST | M2 self-citation | M3 entry doodler | M4 Stolfi template | M5 grille | M5b row-grille |
|---|---|---|---|---|---|---|
| type/token ratio | 0.249 | 0.240 ✓ | 0.201 | 0.398 | 0.326 | 0.282 |
| hapax share of types | 0.687 | 0.552 | 0.414 | 0.587 | 0.484 | 0.496 |
| H2\|1 (bits) | 2.126 | 2.805 | 2.769 | 3.030 | 2.885 | 2.945 |
| final-char H (bits) | 2.540 | 2.933 | 3.738 | 3.164 | 3.086 | 3.151 |
| Zipf slope | −1.072 | −0.858 | −0.712 | −0.614 | −0.631 | −0.772 |
| word length | 4.94 | 3.75 | 3.83 | 5.15 ✓ | 5.13 ✓ | 5.13 ✓ |
| adjacent Jaccard | 0.0975 | 0.0964 ✓ | 0.1031 ✓ | 0.034 | 0.040 | 0.064 |
| distant Jaccard | 0.0647 | 0.0774 ✓ | 0.0554 ✓ | 0.021 | 0.022 | 0.050 ✓ |
| page-unique share | 0.242 | 0.133 | 0.294 | 0.572 | 0.463 | 0.462 |
| **composite on TEST** | | **0.694** | 0.765 | 1.874 | 1.429 | 1.136 |
| selected configuration | | pnew=0.05, rec=2.0, verbatim=0.6 | carry=0.7, topic=30, prime=2, reuse=0.6 | carry=0.5, topic=60, reuse=0.6 | K=40, carry=0.5, reuse=0.6 | K=1000, o=(2,5), reuse=0.6 |

## Held-out results, treatment M (uncertain spaces merged, the pilots' choice)

| Metric | real TEST | M2 | M3 | M4 | M5 | M5b |
|---|---|---|---|---|---|---|
| type/token ratio | 0.297 | 0.353 | 0.280 ✓ | 0.354 | 0.353 | 0.292 ✓ |
| hapax share of types | 0.718 | 0.634 | 0.453 | 0.536 | 0.513 | 0.501 |
| H2\|1 | 2.142 | 3.044 | 2.805 | 3.041 | 2.872 | 2.908 |
| final-char H | 2.480 | 3.312 | 3.754 | 3.104 | 3.004 | 3.116 |
| Zipf slope | −1.033 | −0.775 | −0.624 | −0.620 | −0.626 | −0.767 |
| word length | 5.31 | 3.77 | 4.22 | 5.17 ✓ | 5.30 ✓ | 5.37 ✓ |
| adjacent Jaccard | 0.081 | 0.075 ✓ | 0.069 ✓ | 0.038 | 0.035 | 0.059 |
| distant Jaccard | 0.050 | 0.055 ✓ | 0.041 ✓ | 0.018 | 0.019 | 0.048 ✓ |
| page-unique share | 0.288 | 0.216 | 0.355 | 0.572 | 0.498 | 0.465 |
| **composite on TEST** | | **0.745** | 0.818 | 1.445 | 1.260 | 0.844 |

## What this does to the family's story

1. **The progressive-improvement narrative does not survive.** In PRs #3–#6 each new
   mechanism "beat every earlier model" (composite 0.94 for M4, 0.50 for M5b). On a clean
   target with held-out scoring the order is reversed: the simplest content-free model,
   pilot 1's self-citation doodler, is best, and the Stolfi-template model is worst. The
   flagship grille's 0.50 becomes 1.14 (S) or 0.84 (M).
2. **No model reproduces any of the three entropy/Zipf residues, in either treatment.**
   H2|1 is 0.6–0.9 bits too high, final-char entropy 0.4–1.3 bits too high, Zipf slopes
   0.2–0.4 too shallow. That part of the family's residue claim is confirmed, more strongly
   than before because it now holds out of sample.
3. **The claimed page-structure and vocabulary matches were partly artefacts.** The
   topic-engine models (M4, M5, M5b) produce 46–57 % page-private types against a real
   24–29 %, and adjacent Jaccard 0.03–0.06 against 0.08–0.10. Only M2 and M3 match the
   neighbour metrics, and they do it while being far too repetitive at letter level (short
   words, low hapax share). No model comes within 0.06 of the hapax share.
4. **A dead parameter in pilot 1.** In `gen_m2` the branch order makes fresh invention
   unreachable: the mutation branch fires whenever `r < p_verbatim + (1 − p_new)`, which is
   ≥ 1.2 for every grid value, so `p_new` has no effect and the 27-point grid is really
   9 points (the three `p_new` values give identical composites, see `grid` in
   results.json). M2 never invents a word after the first token; everything is mutation or
   reuse of earlier words.
5. **Selection is unstable.** Under S, M2's best and fourth-best configurations differ by
   0.0014 in FIT composite yet produce H2|1 of 2.81 vs about 3.0; under M a different one
   wins. "Best configuration" statements in the pilots carried no such caveat.
6. **The alternating split makes R5.3 weak.** FIT and TEST halves differ by under 2 % on
   every real metric, so "GENERALISES" only says the selected configuration was not tuned to
   page-specific noise. It does not rescue the models.

### Exploratory (not in the protocol): the family's own procedure on the clean target

Habit tables from all pages, selection and scoring on all pages — the pilots' procedure,
only the parser changed. Best composites: S — M3 0.756, M2 0.819, M5b 1.027, M5 1.227,
M4 1.689; M — M2 0.676, M5b 0.735, M3 0.776, M5 1.003, M4 1.268. So most of M5b's apparent
fit (0.50 → 1.03 under S) was the contaminated target; held-out scoring adds the rest
(1.03 → 1.14). One exploratory curiosity: under M, in-sample M2 with 60 % verbatim reuse
reaches H2|1 2.50 and final-char H 2.57, the closest any content-free model has come to
the entropy residue — by copying a few long merged compounds many times. Its hapax share
(0.51 vs 0.72) shows what that costs. Not a result; a pointer.

## A2′ — cipher advocate with corrected gates

Gates against the clean manuscript under the same treatment: ttr ± 0.03, H2|1 ≤ ref + 0.20,
final-char H ≤ ref + 0.20, word length ± 1.0, Zipf ± 0.15. Reference S: ttr 0.207, H2|1 2.14,
final 2.52, length 4.94, Zipf −1.08. Twelve ciphers × two treatments, all reported.

| Plaintext, cipher (treatment S) | ttr | H2\|1 | final H | length | Zipf | gates passed |
|---|---|---|---|---|---|---|
| Latin, verbose fixed (k=1) | 0.204 ✓ | 2.31 ✓ | 2.76 ✗ (+0.04 over gate) | 11.1 ✗ | −0.97 ✓ | 3/5 |
| Latin, abbreviated fixed | 0.153 ✗ | 2.17 ✓ | 2.67 ✓ | 7.0 ✗ | −1.05 ✓ | 3/5 |
| Latin, k=2 / k=3 homophones | 0.52 / 0.62 ✗ | 2.52 / 2.69 ✗ | 2.96 / 3.17 ✗ | 11.9 / 12.1 ✗ | ✗ | 0/5 |
| Latin, abbreviated k=2 / k=3 | 0.35 / 0.44 ✗ | 2.46 / 2.64 ✗ | 2.91 / 3.19 ✗ | 7.5 / 7.6 ✗ | ✗ | 0/5 |
| Culpeper, verbose fixed | 0.093 ✗ | 2.29 ✓ | 2.73 ✗ | 9.4 ✗ | −1.06 ✓ | 2/5 |
| Culpeper, abbreviated fixed | 0.082 ✗ | 2.23 ✓ | 2.44 ✓ | 6.7 ✗ | −1.11 ✓ | 3/5 |
| Culpeper, homophonic variants | 0.25–0.46 | 2.42–2.68 ✗ | 2.86–3.15 ✗ | 7.1–10.2 ✗ | mixed | ≤ 2/5 |

R6.1: **NOT REPRODUCED BY 12 UNTUNED CIPHERS.** The binding constraint is word length
against type ratio: a verbose cipher that keeps the plaintext's type ratio makes words
twice too long; abbreviating the plaintext brings length toward the manuscript but drops
the type ratio to 0.15; adding homophones restores the type ratio and immediately destroys
both entropy residues. This is a real constraint on any content hypothesis, stated for the
first time in this family: **an encoding of a real text must deliver five-glyph words,
a 70 % hapax share and H2|1 ≈ 2.1 at once.** None of the simple ciphers does. The critique's
earlier component-wise point stands — the two entropy residues alone are cheap to fake —
but the joint fingerprint is not.

## Where things stand after the re-run

- The content-free generators in the family reproduce at most 3 of 9 clean held-out
  properties, never the entropy or Zipf residues, and never the hapax share.
- Simple verbose ciphers of real texts reproduce the entropy residues but not the joint
  fingerprint.
- Both sides now face the same three-way constraint: short words, very high hapax share,
  very low conditional entropy. Whatever produced the text did all three; nothing tested so
  far does.
- The pilots' published numbers, rankings and "best model" claims should be read as
  superseded by the tables above.

## Deviations from the protocol (recorded)

1. `gen_m2` was replaced by `gen_m2_fast`, which uses a Fenwick tree for the verbatim pick
   instead of an O(types) scan. Identical random draws and identical selection; equality
   with the vendored original is asserted on 3,000 tokens at every start-up. Without it the
   M2 grid would have taken over an hour.
2. M3's own pilot selected on ten keys (adding first-char H); the protocol's nine-key family
   composite was used for all models, as written.
3. The in-sample-on-clean-target comparison (`insample_clean.py`) was added after the
   protocol and is labelled exploratory.
4. The dead-parameter finding (item 4 above) was not pre-registered; it was noticed from the
   identical composites in the grid output and is reported as an observation.

## Reproduction

```
python clean_rerun.py --repo ../.. --lab <dir with bibles/Latin.xml and pg49513.txt> --out results/
python insample_clean.py --repo ../.. --out results/     # exploratory
```

Stdlib only; deterministic (seed 408; distant-page sampling seed 7). Runtime about one
minute per treatment.
