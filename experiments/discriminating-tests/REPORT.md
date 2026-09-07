# Two discriminating tests — results

**Protocol:** [PROTOCOL.md](PROTOCOL.md), committed before the run (`09e8f8d` on this branch; first committed as `318a679` on the critique branch).
**Script:** `discriminating_tests.py`; exploratory `exploratory_contentwords.py`.
**Output:** `results/results.json`, `results/stdout.txt`, `results/exploratory_contentwords.json`.
**Run record:** `experiments/runs/2026-09-07T110000Z-discriminating-tests/`.

**Hypotheses credited.** T2 answers a hypothesis proposed by Vasily Gnuchev (7 September 2026):
that the manuscript's letter-pair predictability exists because two (or three) EVA letters
are really one glyph. T1 was the test the critique had listed as the only one on the list
able to separate content from device; Vasily Gnuchev asked for it to be run.

## Verdicts by the frozen rules

| Rule | Result |
|---|---|
| R7 (illustration-linked vocabulary) | **UNDERPOWERED** — the positive control fails its gate (Culpeper related-plant entries: p = 0.44). No substantive label can be attached to the manuscript result. |
| R8.1 (re-segmentation) | **SEGMENTATION-DEPENDENT** — at a data-chosen alphabet of 40 symbols the gap to the lowest language is 0.15 bits; at 50 it is 0.07; at 60 it is 0.09. |
| R8.2 (crossover) | Alphabet size **45** (20 merges): manuscript 3.089 bits = Greek at the same size. |

---

## T2 — Data-chosen re-segmentation (hypothesis: V. Gnuchev)

Byte-pair-style merging of the most frequent word-internal symbol pair, applied identically
to every corpus at 35,000 tokens; H2|1 with the family's formula after each merge.

### The manuscript's first 25 merges (frequency criterion)

`ch dy ai ok ol ee sh in che aiin ot ar al qok or she eey ain daiin chedy ody eedy edy chy qot`

Association criterion (most mutually predictable pair, count ≥ 0.1 %):
`ch sh in iin dy da daiin qo qok ol ee che she cho ka ar al aiin ain ai am dal kaiin kal kain`

For comparison, Greek's first merges are `το αι ει και ου εν του`, Latin's `er et qu it in um us`,
English's `he the an and ou in re`.

### H2|1 at equal alphabet size (primary comparison)

| Alphabet size | Voynich S | Voynich M | Lowest language | Gap S | Latin | Finnish | English |
|---|---|---|---|---|---|---|---|
| 25 (raw EVA) | 2.137 | 2.148 | Greek 3.089 (its raw alphabet is already 45) | 0.95 | 3.323 | 3.246 | 3.188 |
| 30 | 2.437 | 2.459 | Greek 3.089 | 0.65 | 3.475 | 3.477 | 3.360 |
| 40 | 2.938 | 2.980 | Greek 3.089 | **0.15** | 3.667 | 3.679 | 3.484 |
| 50 | 3.196 | 3.251 | Greek 3.261 | **0.07** | 3.770 | 3.784 | 3.561 |
| 60 | 3.366 | 3.414 | Greek 3.455 | **0.09** | 3.827 | 3.849 | 3.578 |

### H2|1 at equal number of merges (secondary)

| Merges k | Voynich S | Greek | Italian | English | Finnish | Latin | Russian | Gap S to lowest |
|---|---|---|---|---|---|---|---|---|
| 0 | 2.137 | 3.089 | 3.162 | 3.188 | 3.246 | 3.323 | 3.465 | 0.95 |
| 10 | 2.701 | 3.357 | 3.378 | 3.445 | 3.576 | 3.573 | 3.629 | 0.66 |
| 20 | 3.089 | 3.526 | 3.501 | 3.527 | 3.724 | 3.713 | 3.734 | 0.41 |
| 40 | 3.412 | 3.686 | 3.689 | 3.589 | 3.866 | 3.856 | 3.870 | 0.18 |
| 60 | 3.597 | 3.763 | 3.806 | 3.635 | 3.936 | 3.938 | 3.934 | 0.04 |

Sensitivity (association criterion): gaps 0.68 / 0.24 / 0.21 / 0.21 at sizes 30 / 40 / 50 / 60;
no crossover within 60 merges for treatment S.

### Reading

1. **By the frozen rule the letter-pair anomaly is segmentation-dependent.** Twenty
   frequency-chosen merges — which are the familiar Voynich word pieces — bring the
   manuscript to 3.09 bits, the value of the lowest language at the same alphabet size.
2. **Two honest caveats.** The crossover is against Greek, whose 45 raw "letters" include
   accented vowels: Greek is itself over-segmented by the tokeniser in the same sense. Against
   Latin, Finnish, Italian and English at matched size the manuscript stays 0.2–0.6 bits lower
   through 60 symbols. And the association criterion, which merges only mutually predictable
   pairs, closes the gap less (0.21 bits at 50–60 symbols).
3. **What is robust across criteria:** the manuscript's excess predictability is
   concentrated in a few dozen fixed letter groups. With 60 merges the gap to every language
   is under 0.1 bit. The earlier statement "far beyond any language" must be restated as
   "far beyond any language at the EVA letter level; language-like at a 45–60-symbol inventory".
4. **What the measurement cannot say:** whether those fixed groups are single glyphs (the
   hypothesis tested here), cipher groups (a verbose cipher makes exactly such groups) or device
   fragments (a table-and-grille makes them too). All three predict this curve. The
   discriminating oddities move to the word level: ~5-glyph words with a 68–72 % hapax share.

---

## T1 — Illustration-linked vocabulary

### T1a. Same plant, two texts

Twelve usable pairs (f48r → f89v2 row 3 has no paragraph; f18v/f23r point to f102r2 row 3,
which is real once labels with illegible glyphs are kept as row markers). Two herbal pages
(f39r, f48v) are Currier B while all pharmaceutical pages are A; for those the null used all
rows, flagged.

| Herbal page → pharmaceutical row | Jaccard | null mean | share of null rows at or above |
|---|---|---|---|
| f1v → f102r1[3] | 0.038 | 0.065 | 0.77 |
| f18v → f102r2[3] | 0.030 | 0.047 | 0.86 |
| f19r → f102v1[2] | 0.011 | 0.051 | 1.00 |
| f23r → f102r2[3] | 0.051 | 0.066 | 0.71 |
| f32v → f102r2[1] | 0.076 | 0.058 | 0.26 |
| f37v → f102r1[3] | 0.050 | 0.051 | 0.54 |
| f39r (B) → f95r2 | 0.098 | 0.059 | 0.03 |
| f47v → f102r2[1] | 0.040 | 0.060 | 0.74 |
| f48v (B) → f89v1[1] | 0.067 | 0.039 | 0.06 |
| f90v2 → f100r[1] | 0.070 | 0.079 | 0.60 |
| f90v1 → f100r[1] | 0.055 | 0.077 | 0.83 |
| f96v → f99r[4] | 0.022 | 0.033 | 0.86 |

S1 mean 0.051 vs permutation null 0.057 ± 0.006, **p = 0.85**; mean percentile 0.61. The
shared words are the corpus's commonest (`daiin`, `chol`, `or`, `ol`, `chey`). S2 (plant label
found in the herbal text): 3 of 5 label sets hit, 2.5 expected by chance; the hits are `sar`,
`char`, `otoy`, all frequent words. Treatment M: p = 0.76.

### T1b. Similar plants by external identification

79 herbal pages with usable name tokens; 28 similar pairs from clusters thistle (6 pairs),
scabiosa (3), boragine (3), primulaceon (3), and single pairs for crassulatea, Herba Paris,
cucumber, polygonum, silene, hemp, tamus communis, smilax, artemisium, arum, artichoke, lunaria.

| | S3 (mean Jaccard) | null mean ± sd | p |
|---|---|---|---|
| label-shuffle null N3 | 0.0846 | 0.0805 ± 0.0051 | 0.21 |
| distance-matched null N4 | 0.0845 | 0.0958 ± 0.0044 | 0.996 (z = −2.6) |

Similar-plant pages share, if anything, *less* than other pages at the same folio distance.
Treatment M: N3 p = 0.07, N4 p = 0.98. Detectable excess at p = 0.05: 0.008 Jaccard (10 % of
the mean).

### Positive control — and why the verdict is UNDERPOWERED

Culpeper's herbal, 96 entries with usable headword tokens, 15 related pairs (four mustards,
three cresses, two saxifrages, two thistles, alders, one-blades, worts, winter-plants).
S3 0.2045 vs N3 0.2011 ± 0.0216, **p = 0.44**; N4 p = 0.53. In a real herbal, entries about
related plants share no more whole-entry vocabulary than random entries by this statistic:
every Culpeper entry is dominated by the same "virtues" vocabulary. The method cannot detect
topic even where topic exists, so the manuscript result carries no weight either way.

### Exploratory (not in the protocol): size-corrected lift with frequent words removed

Lift = shared types / expected under independence given both set sizes. Remove the K most
frequent types of each corpus from every set (a symmetric filter needing no knowledge of the
language).

| K removed | Control lift obs vs null (p, N3 / N4) | Manuscript lift obs vs null (p, N3 / N4) |
|---|---|---|
| 0 | 9.9 vs 7.8 (0.06 / 0.05) | 4.8 vs 4.8 (0.45 / 1.00) |
| 50 | 9.4 vs 7.2 (0.03 / 0.01) | 2.5 vs 2.2 (0.18 / 0.94) |
| 100 | 9.1 vs 6.7 (**0.012 / 0.002**) | 1.6 vs 1.5 (0.33 / 0.97) |
| 200 | 8.8 vs 5.9 (**0.002 / < 0.001**) | 0.83 vs 0.84 (0.49 / 0.91) |

With the 100–200 most frequent words removed and a size-corrected statistic, related Culpeper
entries share about 50 % more content vocabulary than random entries, while the manuscript's
similar-plant pages share none (and sit below their distance-matched null). This is the form
in which the test has power. It is exploratory here; **T1 v2** should pre-register the lift
statistic with K = 100 and the same nulls, and then it will count.

---

## Deviations from the protocol (recorded)

1. Run 1 crashed: two herbal pages are Currier B and no pharmaceutical row is B; the null now
   falls back to all rows, flagged per pair.
2. Row numbering on pharmaceutical pages was wrong when a label's only token contained an
   illegible glyph (the locus was dropped and rows merged); empty label loci are now kept as
   row markers. f18v/f23r → f102r2 row 3 became usable.
3. Run 2 showed the control's similar pairs dominated by the headword token "chapter" (861 of
   877 pairs) and roman numerals; both stop-listed. The control then has 15 pairs.
4. `results.json` is written as UTF-8 (Greek and Cyrillic merge symbols).
5. The lift statistic and the frequent-word-removed variant were added after seeing run 2;
   labelled exploratory throughout.

## Reproduction

```
python discriminating_tests.py --repo ../.. --lab <dir with bibles/ and pg49513.txt> --out results/
python exploratory_contentwords.py --repo ../.. --lab <same> --out results/
```

Stdlib only; deterministic (seed 408); about four minutes.
