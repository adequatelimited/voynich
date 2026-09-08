# Controls extension: is "30% entry-private words" really un-encyclopedic?

## In plain words

**IDEA** (hypothesis contributed by Vasily Gnuchev, 2026-09-07)
- We said: the manuscript keeps 30% of each page's words private to that page — ten times
  a real encyclopedia (Culpeper, 2.8%). Case closed?
- But maybe Culpeper is the wrong comparison — it is dense professional prose from 1653.
  What about a **dictionary**? Or a **children's encyclopedia** with short, simple entries?

**TEST METHOD**
- Measured two more real reference genres with the identical ruler:
  - *The Devil's Dictionary* (Bierce, 1906): 878 short dictionary entries.
  - *The Wonder Book of Knowledge* (1921): a popular/children's encyclopedia,
    164 Q&A entries ("What is a Geyser?").

**ACTUAL RESULT**

| Genre | Entries | Private words per entry | Neighbor sharing |
|---|---|---|---|
| Scholarly encyclopedia (Culpeper, 1653) | 138 | 2.8% | 0.213 |
| Kids' encyclopedia (Wonder Book, 1921) | 164 | **8.0%** | 0.096 |
| Dictionary (Devil's Dictionary, 1906) | 878 | **13.8%** | 0.063 |
| Narrative (Alice) | 165 | 7.2% | 0.196 |
| **Voynich manuscript** | 226 | **30.2%** | **0.080** |

**WHAT IT MEANS**
- The contributor's intuition was right: the gap was partly an artifact of the comparison
  text. Simpler, shorter entries → more private vocabulary. The kids' encyclopedia sits
  three times closer to the manuscript than the scholarly one, and the dictionary's
  neighbor-sharing (0.063) is nearly identical to the manuscript's (0.080).
- The manuscript is still the extreme of the ladder — but it is now visibly *on* the
  ladder, not off it. A short-entry reference work in an encoded or invented vocabulary
  would land roughly where the manuscript sits.
- This slightly **strengthens** the "real content, encoded" branch and slightly
  **weakens** our earlier "the doodler overshoot proves device" reading.

**SO IT IS "THIS" (updated judgment)**
- Strict system/device, decorative: **~55%** (down from 65)
- Real content, encoded: **~35%** (up from 30 — short-entry genres legitimize the
  entry-private vocabulary)
- Plain natural language: **~8%**
- Formless fun: **~2%**

*Percentages: informal judgment after four pilots plus a four-genre control ladder.*

---

## Technical summary

**Pilot 3b (controls extension) in the generative-falsification family.**

- New controls parsed with documented rules: Devil's Dictionary entries split at
  `HEADWORD, pos.` lines (≥8 tokens); Wonder Book entries split at question-style
  headings (≥40 tokens); Culpeper and Alice as in pilot 3.
- Same metric suite as pilots 2–4 (entry metrics subset), same corpus (ZL3b, pinned),
  same distant-pair sampler (seed 7).

Entry-private vocabulary shares: Voynich 0.302, Devil's Dictionary 0.138, Wonder Book
0.080, Alice 0.072, Culpeper 0.028. Neighbor Jaccard: Voynich 0.080, Devil 0.063,
Wonder 0.096, Alice 0.196, Culpeper 0.213.

## Findings

1. **Entry-private vocabulary is genre- and length-dependent.** Shorter, simpler entries
   hold more private types. The dictionary — the most entry-fragmented real genre — is
   the manuscript's nearest real-text neighbor on both entry metrics.
2. **The manuscript remains the extreme,** but on a continuum with real short-entry
   genres rather than an order of magnitude away from all of them.
3. **Correction to pilot 3's emphasis:** the entry-private overshoot of device models
   (38% vs 30%) is weaker evidence against content than stated there, because real
   encoded short-entry text would also elevate private share. The H2|1 and final-char
   residues are unaffected by this correction.
4. **Controls ladder completeness:** four real genres now span the reference-text space
   (dictionary / kids' encyclopedia / scholarly encyclopedia / narrative); further
   refinement should target medieval Latin/Italian for era match, not more English genres.

## Limitations

- Devil's Dictionary entries are satirical definitions — real headword entries, but
  register is humorous prose; parse rules and thresholds are documented in code.
- Wonder Book entries include occasional narrative question lines (~1% noise).
- All controls English; medieval-language control still open.
- Percentages in plain-words section are judgment, not measurement.

## Reproduce

```sh
python controls_entry.py --corpus ../../data/corpora/ZL3b-n.txt \
  --culpeper ../../data/corpora/pg49513.txt --alice ../../data/corpora/pg11.txt \
  --devil ../../data/corpora/pg972.txt --wonder ../../data/corpora/pg41111.txt \
  --out results/
```
