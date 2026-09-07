# Adversarial critique of the generative-falsification family — pre-registered protocol

**Status:** written and committed BEFORE the adversarial script was run. The decision rules
below are frozen; the report applies them mechanically. Any deviation is recorded in the
report under "Deviations".

**Role:** the critic. Every experiment here is designed to *damage* a specific claim made in
PRs #3–#9 (generative doodler, entry doodler, M4 template, M5 grille, controls ladder, poetry
control, languages control). The family's own claims are the targets; the family's own metric
definitions are reused unchanged wherever a target number is being re-examined.

**Corpus:** `data/corpora/ZL3b-n.txt` (sha256 in `data/manifests/zl3b.json`). Controls already
in the repo or in the local lab: Culpeper (PG 49513), Alice (PG 11), nine Bible translations
(Christodoulopoulos & Steedman bible-corpus, hashes in `experiments/languages-control/
source_hashes.json`), plus two new Chaucer editions fetched today (hashes recorded in
`results/source_hashes.json`).

**Sampling constant:** 35,000 tokens for every same-size comparison (the family's constant).

---

## A0 — Parser-contamination audit

**Target claims.** All headline numbers of the family are computed by one shared parser
(`load_pages` / `load_corpus` / `load_voynich`): 34,986 tokens, 10,120 types, ttr 0.289,
H2|1 2.26, final-glyph entropy 2.58/2.59, "richest vocabulary of all".

**Adverse hypothesis.** The parser leaves IVTFF mark-up inside tokens (paragraph markers
`<%>`/`<$>` reduced to `%`/`$` and glued to words, `[a:b]` alternative readings kept verbatim,
`<->` gap markers gluing two words into one, `?` illegible glyphs deleted so that a new
pseudo-type is created, `@nnn;` extended-glyph codes reduced to fragments). If so, the type
count and the character entropies are contaminated and the doodlers were fitted to a
contaminated target.

**Method.** Re-parse with a documented clean parser: strip every `<…>` tag (`<->` becomes a
word boundary), strip `{…}`, resolve `[a:b]` to the first alternative (the transcriber's
preferred reading), split on `.`, whitespace and `,` (uncertain space treated as a space;
sensitivity run with `,` as no-space), drop any token containing `?`, `@` or a digit, keep only
`[a-z]+` tokens. Recompute the family's metrics with the family's formulas on the clean
tokens, side by side with the as-published parser.

**Decision rules (frozen).**
- R0.1 If clean types differ from the published 10,120 by more than 3 % (i.e. outside
  9,816–10,424), the family's numbers are declared **CONTAMINATED** and must be restated.
- R0.2 The claim "richest vocabulary at equal size" survives only if clean Voynich types at
  ≤ 35,000 tokens still exceed every control computed with the same `[a-z]+`, no-length-filter
  tokenisation (the family's English tokeniser drops 1-letter words while the Voynich
  tokeniser keeps them; both variants are reported).

## A1 — Transcription-alphabet confound

**Target claims.** "No language approaches the letter-pair constraint (H2|1 2.26 vs nearest
Greek 3.14)"; "no language approaches the final-glyph entropy (2.58 vs nearest Finnish 2.80)".

**Adverse hypothesis.** EVA spells single glyphs with several Latin letters (`ch`, `sh`,
`cth`, `ckh`, `cph`, `cfh`, arguably `iin`/`in`/`ee`). Inside such a spelling the next letter is
nearly determined, which depresses H2|1 by construction. The languages were measured in
their native one-letter-per-grapheme orthographies, so the comparison is between alphabets
of different granularity.

**Method.** Three alphabet levels for the manuscript: (a) raw EVA, (b) benched gallows and
`ch`/`sh` merged to single symbols, (c) level (b) plus `iiin`, `iin`, `in`, `ii`, `eee`, `ee`.
Then an **identical, data-driven** treatment for every corpus (manuscript and all nine
languages and the English controls): iteratively merge the word-internal symbol pair (x,y)
with the highest count among pairs satisfying P(y|x) ≥ 0.90 and count ≥ 0.1 % of all symbols,
until none qualifies ("determinism merge"). Recompute H2|1 (space-joined, family formula) and
final-symbol entropy at every level.

**Decision rules (frozen).**
- R1.1 The H2|1 anomaly is **ALPHABET-ROBUST** if, after level (b) for the manuscript (the
  uncontroversial single-glyph merges; Latin-alphabet languages need no equivalent because
  their letters are already single graphemes) followed by the identical determinism merge
  for every corpus, the manuscript's H2|1 is still ≥ 0.30 bits below the lowest language. If
  the gap is < 0.30 bits the claim is downgraded to **ALPHABET-DEPENDENT**. Level (c) +
  determinism merge is reported as a sensitivity, without a gate.
- R1.2 The final-glyph anomaly is **ALPHABET-ROBUST** if, at level (c), the manuscript's
  final-symbol entropy is still ≥ 0.20 bits below the lowest language's raw final-letter
  entropy (level (c) can only raise the manuscript's value, so this is the conservative
  direction). Otherwise **ALPHABET-DEPENDENT**.

## A2 — Advocate for the content side: enciphered real texts

**Target claims.** "Fake text by a strict fixed system ~55–65 %"; "the residue (H2|1,
final-glyph entropy, vocabulary richness) is what device models cannot yet fake".

**Adverse hypothesis.** The residue is exactly what a verbose or homophonic cipher of a real
text produces: fixed glyph groups depress H2|1, group endings depress final-glyph entropy,
homophones inflate the type count. If an enciphered real herbal lands on the residue, the
residue does not discriminate "device" from "encoded content" and the family's central
judgment loses its evidential base.

**Method.** Plaintexts: Culpeper's herbal entries (real entries, gives page metrics) and the
Latin Vulgate (first 35,000 tokens). Cipher families, all built **without tuning** by
frequency-rank assignment from the clean manuscript (the same corpus-derived advantage the
doodlers were given):
- C1 monoalphabetic (sanity: must reproduce plaintext statistics up to relabelling);
- C2 verbose fixed: plaintext letter of rank i → word-internal EVA 2–3-gram of rank i;
- C3 verbose homophonic: letter of rank i → 2-3-grams of ranks i, i+26, i+52, chosen at
  random weighted by n-gram frequency (seed 408);
- C4 abbreviated homophonic: non-initial vowels dropped from the plaintext (scribal
  abbreviation), then C3;
- C5 positional: first letter → left fragment of rank i, last letter → right fragment of
  rank i (fragments by the M5 Stolfi-layer split), middle letters → C1 letters.
Full metric suite on every ciphertext, including the determinism-merged H2|1 from A1.

**Decision rules (frozen).**
- R2.1 The residue is declared **NON-DISCRIMINATING** if any cipher of a real text
  simultaneously satisfies: H2|1 ≤ 2.56 (raw EVA level), final-symbol entropy ≤ 2.90 and
  ttr within [0.22, 0.32] at ≤ 35,000 tokens.
- R2.2 If no cipher satisfies R2.1, the record is **NOT REPRODUCED BY TESTED CIPHERS** —
  explicitly weak evidence, because the cipher space is unbounded and only five untuned
  families were tried. This asymmetry is part of the protocol.
- R2.3 Word length is reported but is *not* a gate: verbose ciphers are known to lengthen
  words, and the plaintext could be abbreviated (C4 tests that partially).

## A3 — Structure claims against nulls and confounds

**Target claims.** "Neighbouring pages share 2× more vocabulary than distant pages (0.080 vs
0.042): topical organisation is measurable fact, encyclopedia structure ~90 % confirmed";
"30 % of each page's word types are private to the page, ten times a real encyclopedia".

**Adverse hypotheses.** (i) The page-private share is a consequence of hapax richness, not
of entry structure: any corpus in which 70 % of types are hapaxes will show ~30 % page-private
types under random assignment. (ii) The adjacent/distant contrast is a Currier-language and
section confound: adjacent pages are almost always in the same language and section, while
"distant" pages (folio distance > 20) usually cross both. (iii) Label loci (single-word
labels on astronomical/zodiac pages) were pooled with paragraph text. (iv) Controls were not
size-matched: Culpeper has several times more tokens, which mechanically lowers its
entry-private share.

**Method.** 200 token permutations across pages preserving page sizes → null distributions
of adjacent Jaccard, distant Jaccard and page-unique share. Adjacent/distant Jaccard restricted
to page pairs sharing `$L` and `$I`, distant = same `$L`, same `$I`, folio distance ≥ 5.
Paragraph-loci-only (`P`) variant. Controls truncated to 35,000 tokens for the page-unique
share.

**Decision rules (frozen).**
- R3.1 "Topical organisation" survives if the within-language-within-section
  adjacent/distant ratio is ≥ 1.30 AND the observed adjacent Jaccard exceeds the 97.5th
  percentile of the permutation null. Otherwise it is relabelled **LANGUAGE/SECTION ARTEFACT**.
- R3.2 "30 % page-private is anomalous structure" survives only if the observed page-unique
  share exceeds the permutation-null mean by ≥ 5 percentage points. Otherwise it is relabelled
  **HAPAX-RICHNESS CONSEQUENCE** (the same fact as the high ttr, counted twice).
- R3.3 "Ten times a real encyclopedia" is restated with size-matched controls; the ratio is
  reported, no gate.

## A4 — Medieval-orthography control for vocabulary richness

**Target claim.** "The manuscript has the richest vocabulary of all (10,120 types at equal
size) — odd for language."

**Adverse hypothesis.** All nine Bible translations and all English controls are modern
standardised editions. A 15th-century manuscript has unstandardised spelling; the same word
appears in several spellings, inflating types. The fair comparison is a text in medieval
orthography.

**Method.** Chaucer, *Canterbury Tales*: Skeat's Middle English edition (PG 22120,
unnormalised spelling) versus Purves' modernised-spelling edition (PG 2383) of the same text,
first 35,000 tokens each, same tokeniser as the controls (with and without the 1-letter
filter). Report types, ttr, hapax share of types, final-letter entropy, H2|1.

**Decision rules (frozen).**
- R4.1 If Middle English reaches ttr ≥ 0.25 at 35,000 tokens (clean Voynich ≈ 0.264, see A0),
  the "odd for language" claim is **WITHDRAWN**. If it stays ≤ 0.22 the claim **SURVIVES this
  control**. Between 0.22 and 0.25: **WEAKENED**.
- R4.2 The orthography effect is reported as Skeat ttr minus Purves ttr; no gate.

---

## What is NOT in this protocol

- No new doodler and no new "best model" — a critic who adds a model is doing the family's
  work, not the critic's.
- No probability judgments. The report states, for each rule, which label the data selected.
- Section-by-section exploration (already scripted in `experiments/section-analysis/`) is
  exploratory and is not part of the confirmatory set here.

## Reproduction

```
python adversarial_critique.py --repo ../.. --lab <dir with bibles/ and Chaucer texts> --out results/
```

Stdlib only. Deterministic (seed 408 for homophone choice and 7 for distant-page sampling,
the family's constants). Runtime a few minutes.
