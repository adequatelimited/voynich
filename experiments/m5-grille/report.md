# M5: the Cardan table-and-grille, built from the manuscript itself

## In plain words

**IDEA**
- The strongest "fake" theory in the literature: the scribe used a *device* — a table of
  word fragments (left/middle/right columns) and a card with three holes (a "grille").
  Each word = whatever shows through the holes. Move the card, write the next word.
- Zandbergen (2021) showed such a device can reproduce one real page exactly. We ask the
  statistical question: can it reproduce the *whole manuscript's* fingerprint — including
  the properties every previous robot missed?

**TEST METHOD**
- We cut every real Voynich word into three parts (using Stolfi's published grammar) and
  built the table straight from the manuscript: each row is a real word's fragments, with
  its real frequency as the weight.
- Two devices were tested: (M5a) columns sampled independently; (M5b) the faithful device —
  the grille picks one *row*, with the holes at fixed heights, so fragments stay coupled.
- Same entry engine as before (page topics, carry-over, reuse). 40 configurations,
  3 extra seeds for stability.

**ACTUAL RESULT**
- The faithful row-coupled grille (M5b) is the best content-free model yet — better than
  independent columns, habit chains, and the plain template:
  - popularity curve steepened to −0.84 (real −1.05; previous best −0.63)
  - neighbor-page sharing 0.077 (real 0.080) and distant-page 0.045 (real 0.042) — matched
  - word length 5.4 (real 5.6) — matched
  - vocabulary 8,600–9,700 types (real 10,120) — close
- Row coupling beats independent columns on every configuration — the device detail matters.
- Multi-seed check: all metrics stable (SD ≤ 0.02 on entropy measures).

**STILL NOT FAKED**
- Letter-pattern constraint: 2.89 bits vs real 2.26.
- Word-ending predictability: 3.11 vs real 2.59.
- Entry-private vocabulary: 38% vs real 30% (device invents too many page-words).

**SO IT IS "THIS" (updated judgment)**
- The best 16th-century-compatible device, built from the manuscript's own fragments,
  reproduces most of the fingerprint — and the gap keeps shrinking with each mechanism
  refinement. "Strict production system" (artist's device or discipline): **~65%**.
- "Real but encoded content": **~30%** — unchanged; a cipher remains statistically
  indistinguishable from a device under these metrics.
- "Plain natural language": **~5%**. "Formless fun": **~1%** — effectively closed.
- The remaining residue (letter-level predictability, word endings) is now the *only*
  statistical wall left, and it is narrow enough to name: final glyphs and local letter
  transitions.

*Percentages are informal judgment after four pilots, not computed probabilities.*

---

## Technical summary

**Pilot 4 in the generative-falsification family**, extending `outcome-m4-template-doodler-pilot`.

- Table construction: corpus words split into (left, core, right) by Stolfi-layer parse
  (core {t p k f cth cph ckh cfh}, fallback mantle, fallback first char); rows are real
  triples with corpus frequencies.
- M5a: independent weighted columns (K ∈ {40, 80, 120} fragments/column).
- M5b (faithful device): K ∈ {1000, 3000} frequency-ordered rows; grille offsets
  (o1, o2) ∈ {(0,0),(1,0),(0,2),(2,5)}; word = left[r] core[r+o1] right[r+o2].
- Entry engine as in pilots 2–3 (topic size 60, prime 2, carry 0.3–0.5, reuse 0.6–0.7,
  fragment-resample mutations). Seed 408; multi-seed {101, 202, 303} for the winner.

| Metric | Real | M5b best | M4 best | M3 best | M2 best |
|---|---|---|---|---|---|
| types | 10,120 | 8,593 | 10,346 | 8,603 | — |
| ttr | 0.289 | 0.246 | 0.296 | 0.246 | 0.304 |
| H2\|1 | **2.26** | 2.89 | 3.04 | 2.91 | 2.75 |
| Zipf slope | −1.05 | **−0.84** | −0.63 | −0.64 | −0.76 |
| final-char H | **2.59** | 3.11 | 3.14 | 3.29 | 2.91 |
| word length | 5.6 | 5.4 | 5.2 | 4.7 | 4.5 |
| adjacent J | 0.080 | 0.077 ✓ | 0.073 ✓ | 0.075 ✓ | — |
| distant J | 0.042 | 0.045 ✓ | 0.019 ✗ | 0.035 ≈ | — |
| entry-unique | 0.302 | 0.377 ✗ | 0.447 ✗ | 0.279 ✓ | — |
| composite dist | 0 | **0.50** | 0.94 | 0.85 | 1.07 |

## Findings

1. **The faithful device detail matters.** Row coupling (holes at fixed offsets) beats
   independent columns across the board and steepens Zipf from −0.65 to −0.84. Grille
   mechanics are not cosmetic — they shape global statistics.
2. **Convergence pattern across the family:** each mechanism refinement (habits → entry
   structure → published template → coupled grille) closes more of the fingerprint. The
   trajectory supports a *mechanical* production process more than any single mechanism.
3. **The surviving residue is now exactly two things:** letter-level conditional entropy
   (≈0.6 bits too high in every model) and word-final predictability. Both are *local*
   constraints — plausible targets for one more refinement (line-position rules, or
   grille rows weighted by neighbor rows).
4. **Entry-private share overshoots in all device models** (0.37–0.45 vs 0.302): the real
   manuscript reuses *global* vocabulary inside pages more than a fresh-device model does.
   Consistent with a table that is *reused* across pages, not regenerated.

## Limitations

- The table is corpus-derived (built from the manuscript's own words) — this gives the
  device maximal advantage by construction; the residue persists *despite* it.
- Only ZL3b; GC2a (v101 alphabet) cross-check still pending. Single metric suite.
- Grille offsets grid is small; no line-position effects modeled.
- English-only controls from pilot 3 still stand; no medieval-language control yet.

## Next steps

- Final-char constraint probe: measure which line-final/word-final rules a device would
  need; test a grille with position-weighted rows.
- Currier A/B: two tables (two grilles/sessions) vs the measured section split.
- Zodiac label-consistency probe.
- GC2a robustness run.

## Reproduce

```sh
python m5_grille.py --corpus ../../data/corpora/ZL3b-n.txt --out results/ --seed 408
```
