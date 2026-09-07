# Two discriminating tests — pre-registered protocol

**Status:** written and committed BEFORE the script was run. Rules frozen; deviations recorded
in the report.

**Why.** After the critique and the clean re-run, the device reading and the encoded-content
reading are observationally equivalent under the metric family. Two questions from the
human contributor (7 September 2026) point at tests that could move that:

1. *Does the text know what is drawn?* If the text is about the pictures, pages depicting
   the same or similar plants should share vocabulary beyond what neighbour drift, section
   and Currier language predict. A device predicts no such excess.
2. *Is the letter-pair predictability an artefact of over-segmentation?* If two or three
   EVA letters are really one glyph, the low conditional entropy could be a transcription
   artefact. The critique tested two fixed merge sets; this test lets the data choose the
   merges, identically for every corpus, and compares at equal alphabet size.

**Corpus.** ZL3b, clean parser from the critique; uncertain spaces as spaces (S) primary,
merged (M) as sensitivity. Illustration information is taken **only** from the editorial
comment lines of the ZL3b file (Zandbergen's compilation of published plant identifications
and "same plant as" cross-references), never from the text.

---

## T1 — Illustration-linked vocabulary

### T1a. Same plant, two texts (herbal page ↔ pharmaceutical row)

Thirteen herbal pages carry a comment "Same plant as f<page>[row,col]" pointing to a small
plant drawing on a pharmaceutical page. Pharmaceutical pages are organised in rows: a run
of label loci (`Lc` container, `Lf` plant) followed by a paragraph (`P` loci). Row r of the
reference = the r-th such block on that page; a reference without coordinates means the
whole page.

- **Statistic S1 (paragraph sharing):** Jaccard between the herbal page's word-type set and
  the referenced row paragraph's word-type set, averaged over the pairs.
- **Null N1:** the same herbal page against every other pharmaceutical row paragraph in the
  same Currier language (empirical distribution); p = share of null pairs at or above the
  observed pair, combined over pairs by the mean of per-pair percentile ranks and a 5,000-draw
  permutation of row assignments.
- **Statistic S2 (label in text):** for pairs whose referenced row has at least one `Lf`
  label, whether any label token (or any token within edit distance 1 of it) occurs in the
  herbal page's text.
- **Null N2:** the same label tokens against every other herbal page of the same language.

### T1b. Similar plants (herbal page ↔ herbal page)

Eighty-two herbal pages carry a "Plant ID" comment. Normalise each into name tokens:
lowercase, split on non-letters, drop tokens shorter than 4 letters, drop a fixed stop-list
of uncertainty words and author names (listed in the script). Two pages are **similar** if
they share at least one token. Similarity is computed before any text is read.

- **Statistic S3:** mean Jaccard over similar pairs (word-type sets of the full page).
- **Null N3 (label shuffle):** permute the ID comments across the 82 pages within Currier
  language, 5,000 times; recompute S3 on the induced similar pairs.
- **Null N4 (distance-matched):** for each similar pair (i, j), 200 draws of a pair (i, j′)
  with j′ an ID'd page of the same language and |folio(j′) − folio(i)| within ± 3 of the
  original distance; compare the observed mean with the matched-null mean.

### Positive control (power)

Culpeper's herbal entries (PG 49513, ≤ 35,000 tokens as in the critique): two entries are
similar if their headwords share a token ("Water Betony"/"Wood Betony"). Same S3/N3 test.
The method has power if the control's excess is significant at p < 0.01.

### Decision rules (frozen)

- **R7.1** If T1a S1 has p < 0.05 under N1 **and** T1b S3 has p < 0.05 under both N3 and N4,
  and the positive control passes: **ILLUSTRATION-LINKED VOCABULARY DETECTED**.
- **R7.2** If neither reaches p < 0.05 and the positive control passes:
  **NO ILLUSTRATION-LINKED VOCABULARY AT THIS POWER**, with the detectable effect size
  reported (the excess that would have given p < 0.05 with the observed null SD).
- **R7.3** Mixed outcomes (one of T1a/T1b significant): **INCONCLUSIVE**, both reported.
- **R7.4** If the positive control fails: **UNDERPOWERED**, no substantive label.
- S2 is reported with its null but is not a gate (labels may be names that do not recur).

---

## T2 — Data-chosen re-segmentation

For every corpus (Voynich S and M; the nine Bible translations; Culpeper; Alice; all at
35,000 tokens with the same Unicode-letter tokeniser), apply byte-pair-style merging:
at each step merge the most frequent word-internal adjacent symbol pair into one symbol,
for k = 0 … 60 merges. After each merge record: alphabet size, H1, H2|1 (family formula,
space-joined), word-internal H2|1.

- **Primary comparison at equal alphabet size.** For target sizes 30, 40, 50, 60 (linear
  interpolation between recorded steps), gap(size) = lowest language H2|1 − Voynich H2|1.
- **Secondary comparison at equal k.**
- **Sensitivity:** association-based merging (highest min(P(y|x), P(x|y)) among pairs with
  count ≥ 0.1 % of symbols) instead of frequency-based.

### Decision rules (frozen)

- **R8.1** If gap(size) < 0.30 bits at any target size ≤ 60 under the primary comparison:
  **SEGMENTATION-DEPENDENT** — the letter-pair anomaly can be removed by a glyph inventory
  of plausible size. Otherwise **INTRINSIC**.
- **R8.2** The alphabet size at which the manuscript first rises above the lowest language
  (the crossover), if any, is reported; no gate.

---

## Not in this protocol

No image-embedding similarity (would require downloading model weights; the editorial
plant identifications are external, human and already on file). No new generators. No
probabilities.

## Reproduction

```
python discriminating_tests.py --repo ../.. --lab <dir with bibles/ and pg49513.txt> --out results/
```

Stdlib only; deterministic (seed 408).
