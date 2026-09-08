# Multilingual controls: does any real language reach the manuscript's discipline?

## In plain words

**IDEA** (hypothesis contributed by Vasily Gnuchev, 2026-09-07)
- English barely marks word endings. But inflected languages — Latin, Russian, Finnish —
  carry case and number endings. Maybe in such a language, word endings are *naturally*
  as predictable as the manuscript's, and the "unfakeable residue" is just normal
  morphology.

**TEST METHOD**
- The same book (the Bible) in 9 languages — identical content, so every difference is a
  language difference. Equal 35k-token samples (the Voynich corpus size).
- Measured: word-final glyph entropy, letter-pair entropy, vocabulary diversity, word
  length.

**ACTUAL RESULT** (sorted by word-ending predictability)

| Language | Final-glyph entropy | Letter-pair H2\|1 | Types |
|---|---|---|---|
| **Voynich** | **2.58** | **2.26** | **10,120** |
| Finnish | 2.80 | 3.31 | 7,379 |
| Italian | 3.02 | 3.25 | 4,725 |
| Greek | 3.25 | 3.14 | 4,526 |
| Latin | 3.30 | 3.36 | 7,185 |
| German | 3.57 | 3.21 | 3,846 |
| French | 3.57 | 3.31 | 3,738 |
| Spanish | 3.63 | 3.27 | 4,272 |
| English | 3.78 | 3.25 | 2,750 |
| Russian | 4.23 | 3.52 | 6,136 |

**WHAT IT MEANS**
- The morphology idea had real support: Finnish — the most ending-driven language here —
  is the manuscript's nearest neighbor. But even Finnish stops at 2.80 vs 2.58, and no
  language comes close on letter-pair predictability (nearest: Greek 3.14 vs 2.26).
- No tested real language reaches the manuscript on either residual property.
- Surprise 1: Russian — heavily inflected — has the *least* predictable endings (4.23).
  Inflection ≠ predictable endings.
- Surprise 2: the manuscript has the *richest* vocabulary of all (10,120 types at 35k
  tokens; nearest: Finnish 7,379). Odd for language, odd for gibberish — but natural for
  a device that recombines fragments.
- A Russian primer (Tolstoy's Азбука/Букварь genre) was considered as an additional
  control; a clean machine-readable full text was not available from public sources in
  this round — queued as a follow-up (the Russian Bible control covers the language).

**SO IT IS "THIS" (judgment)** — plain natural language weakens further: **~5%**.
Strict system/device ~55%, encoded content ~38% (up slightly: morphology in a known
language is now excluded, but an *encoded* or *invented* language is not), formless fun
~2%. *(Informal judgment, not measurement.)*

---

## Technical summary

Same-text multilingual control (bible-corpus, Christodoulopoulos & Steedman): 9
languages, 35k-token samples, equal to the Voynich corpus size. Metrics identical to
pilots 1–4. The manuscript is the extreme on word-final entropy (2.58), conditional
bigram entropy (2.26) and type/token diversity (0.289 — the *highest* type diversity in
the table). Finnish is its nearest neighbor on endings (2.80) and diversity (0.211);
Greek nearest on H2|1 (3.14). Russian — despite rich inflection — has the *least*
predictable word endings (4.23), showing inflection alone does not produce
manuscript-like discipline.

## Limitations

- Bible register (liturgical/narrative prose) in all languages; genre is held constant
  across languages but is not encyclopedic — cross-checking with inflected-language
  *reference* texts is open.
- Translation rights vary by language in the source corpus: only the public-domain
  Latin Vulgate and English WEB are committed; the other translations are referenced
  with sha256 hashes (`source_hashes.json`), not redistributed.
- 35k-token prefix samples, not verse-matched alignment.
- A requested Russian primer (Tolstoy's Азбука) control is queued; no clean public
  machine-readable full text was available in this round.

## Reproduce

```sh
python languages_control.py --corpus ../../data/corpora/ZL3b-n.txt \
  --bibles <dir with the nine XMLs> --out results/
```
