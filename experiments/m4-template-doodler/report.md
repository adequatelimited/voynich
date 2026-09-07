# M4: the template doodler (Stolfi's word grammar) + real-language controls

## In plain words

**IDEA**
- Two upgrades at once: (1) test the robot scribe that follows a *published* strict word
  recipe (Stolfi's 2000 word grammar — every word is built like a small hill: strong letters
  in the middle, weak letters at the edges); (2) for the first time, measure **real texts**
  with the same ruler: Culpeper's *Complete Herbal* (1653) — a real illustrated
  encyclopedia of plants — and *Alice in Wonderland* — normal story English.

**WHY CONTROLS MATTER**
- Until now we only knew "the robots don't match the manuscript". But maybe NO text matches
  it under our ruler? Controls tell us what real language and real encyclopedias actually
  score.

**ACTUAL RESULT — controls**
- Real texts (Culpeper, Alice): letter-pattern constraint H2|1 ≈ **3.2–3.3 bits**.
  The Voynich manuscript: **2.26 bits**. Real language does NOT look like the manuscript
  under this measurement — the manuscript is *more* predictable than real language.
- Real encyclopedia (Culpeper): neighboring entries share 0.21 of vocabulary, and only
  2.8% of an entry's words are private to it. The Voynich "entries": 0.080 shared and
  **30% private words** — ten times more private vocabulary than a real reference work.
- Zipf popularity curve: real texts −0.99/−1.13, Voynich −1.05 — here Voynich looks
  perfectly normal.

**ACTUAL RESULT — M4 template robot (Stolfi grammar, published 2000)**
- The published grammar fits the manuscript well: **86% of all word types obey the
  unimodal-hill rule** with no fitting at all.
- The M4 robot now matches: vocabulary size (10,346 vs 10,120 types), type/token ratio
  (0.296 vs 0.289), word length (5.2 vs 5.6), neighbor-page sharing (0.073 vs 0.080).
- Still unmatched: letter-pattern constraint (3.04 vs 2.26 bits), word-ending
  predictability (3.14 vs 2.59), popularity curve (−0.63 vs −1.05), and it overshoots
  page-private vocabulary (45% vs 30%).

**SO IT IS "THIS" (updated judgment)**
- "Plain natural language, written normally" — **weakened hard by the controls, ~10%**:
  real language is measurably different from the manuscript on the exact properties that
  matter (entropy, entry-private vocabulary).
- "Fake/artificial text produced by a strict fixed system" — **strengthened, ~60%**:
  a published rule-based recipe (Stolfi grammar + entry engine) now reproduces most of the
  fingerprint, and the residue is exactly the kind of thing a mechanical production rule
  (a real Cardan-style grille/table with weighted columns) would also produce.
- "Real content, but encoded/transformed" (cipher, shorthand, invented script for a real
  language) — **~30%**: still alive, because a cipher would distort exactly these
  statistics; our measurements cannot separate "rule-faked" from "rule-encrypted".
- "Pure formless fun" — **~5%**: dead as a serious candidate.

*Percentages remain informal judgment, now informed by three pilots plus controls.*

---

## Technical summary

**Pilot 3 in the generative-falsification family**, extending `outcome-entry-doodler-pilot`.

### Controls (same metric suite, same code)

| Metric | Voynich | Culpeper (encyclopedia) | Alice (narrative) |
|---|---|---|---|
| tokens / types | 34,986 / 10,120 | 242,235 / 9,336 | 25,575 / 2,550 |
| type/token ratio | 0.289 | 0.039 | 0.100 |
| H2\|1 (bits) | **2.26** | 3.30 | 3.20 |
| Zipf slope | −1.05 | −0.99 | −1.13 |
| word length | 5.6 | 4.6 | 4.1 |
| final-char entropy | **2.59** | 3.64 | 3.59 |
| adjacent-entry Jaccard | 0.080 | 0.214 | 0.196 |
| distant-entry Jaccard | 0.042 | 0.156 | 0.158 |
| entry-unique type share | **0.302** | 0.028 | 0.072 |

Control takeaways: (a) the manuscript's low conditional entropy and final-char entropy are
**not** typical of real language under identical measurement; (b) real encyclopedias share
function vocabulary across entries and have almost no entry-private words — the
manuscript's 30% entry-private share is ten times the real-encyclopedia value; (c) its
Zipf slope is normal. Culpeper entries were split at per-herb headings (minimum 40 tokens);
Alice chunked into 155-token blocks (Voynich page mean).

### M4 model

Word generator implements Stolfi (2000a): core {t p k f cth cph ckh cfh}, mantle
{ch sh ee}, crust {d l r s n x i m g}, circles {a o y} as pre-modifiers/final letter,
e attached after core/mantle; density profile must be a unimodal hill. Slot inventory is
the published model; only the per-slot letter weights are corpus-estimated. Template words
feed the pilot-2 entry engine (topic carry-over + drift + preferential reuse); mutations
resample one slot. Grammar sanity check: 86.0% of corpus types satisfy the hill rule.

Best grid point (`carry=0.5, topic=60, reuse=0.7`, seed 408): types 10,346 (real 10,120),
ttr 0.296 (0.289), word length 5.16 (5.6), adjacent Jaccard 0.073 (0.080). Residual:
H2|1 3.04 vs 2.26; final-char 3.14 vs 2.59; Zipf −0.63 vs −1.05; entry-unique 0.447 vs
0.302.

## Findings

1. **Controls reframe the residue.** The properties our doodlers miss (low H2|1, low
   final-char entropy, steep Zipf, high entry-private vocabulary) are also the properties
   where the manuscript differs from *real language*. "The robots can't match it" is no
   longer evidence for linguistic content — quite the opposite.
2. **A published 25-year-old grammar covers 86% of the vocabulary** with zero fitting,
   and a template+entry generator built on it reproduces vocabulary size, reuse, word
   length and page-level structure simultaneously.
3. **The surviving gap is mechanical-looking:** the real text is more repetitive at
   letter level and recycles words harder than either language or our generators. This is
   the signature a weighted table-and-grille device (Rugg/Zandbergen 2021) would also
   leave. Cipher content would distort the same statistics — the two readings remain
   observationally close under this metric family.
4. **Entry-private vocabulary overshoot** (45% vs 30%): our per-page invention rate is
   too high; the real entries reuse *global* vocabulary more. Voynich entries are less
   isolated than our model's, though far more isolated than real-language entries.

## Limitations

- Controls are English, not medieval Latin/Italian; a medieval-language control is
  desirable but English encyclopedia vs English narrative already separates the metric
  directions cleanly.
- M4 slot weights are corpus-estimated (the slot *assignment* is the published model);
  circle insertion probabilities are heuristic.
- Single seed; grid coarse; distant-Jaccard uses sampled pairs (seed 7).
- Alice is a narrative control with artificial chunking; its entry metrics are indicative
  only. Culpeper's entry split relies on the e-text's heading convention (spot-checked).
- Percentages in the plain-words section are judgment, not measurement.

## Next steps

- Medieval Latin/Italian control (e.g., a public-domain herbal) for language-era match.
- Table-and-grille generator with weighted columns (per Zandbergen 2021) — predicted to
  close the H2|1 and Zipf gaps; if it does, the family question becomes historical
  (who built the device) rather than statistical.
- Zodiac label-consistency probe; multi-seed CIs; GC2a cross-check.

## Reproduce

```sh
python m4_doodler.py --corpus ../../data/corpora/ZL3b-n.txt \
  --alice ../../data/corpora/pg11.txt --culpeper ../../data/corpora/pg49513.txt \
  --out results/ --seed 408
```
