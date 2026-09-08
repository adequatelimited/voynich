# Meaning probes — pre-registration

Pass: `experiments/meaning-probes/`
Branch: `research/meaning-probes`
Written before any test statistic was computed. Gates below are frozen; results
go in `REPORT.md` and `results/`.

## What this pass is for

Every previous pass in this repository asked whether the manuscript's statistics
can be produced by a generative process. None of them tried to read anything.
This pass tries to establish **minor, provable meaning** — the kind of meaning
that can be demonstrated without knowing the language:

1. a counting system (Linear B and Maya both fell to numerals first), and
2. the function of two fixed positions — the paragraph-opening character and the
   label register.

The claim standard is the project's usual one: a gate is stated before the test,
the statistic is computed by a script in this directory, and if the gate fails
the report says so. **No new word meanings are claimed unless a gate passes.**

## Data

| file | role | sha256 |
|---|---|---|
| `data/corpora/ZL3b-n.txt` | primary transcription (Zandbergen–Landini 3b) | `bf5b6d4a…` (recorded in `results/`) |
| `data/corpora/GC2a-n.txt` | independent transcription, replication only | recorded in `results/` |
| `tmp/voynich_lab/pg49513.txt` | Culpeper, *The Complete Herbal* — positive control for L1 | recorded in `results/` |
| built-in | numeral series 1–30 in 8 systems — power calibration for Z1/Z2 | in `meaning_lib.py` |

Parser: `clean_tokens` / `parse_pages` in `meaning_lib.py`, verbatim semantics of
the clean parser fixed by the adversarial critique (protocol `15b6999`). The
contaminated "family" parser is not used anywhere in this pass. Both readings of
the uncertain-space mark `,` are reported wherever the choice can change a number.

Glyph units: the frozen 20 byte-pair merges from T2 (protocol `318a679`,
freq mode, corpus Voynich_S), applied in order:
`ch dy ai ok ol ee sh in che aiin ot ar al qok or she eey ain daiin chedy`.
This is the level at which the manuscript's letter-pair anomaly disappears, so it
is the level at which a linguistic unit is most likely to live. Every test is run
at glyph-unit level and, as a robustness check, at raw EVA-character level.

## Reconnaissance already performed (disclosed)

Before writing this file the following **structural** counts were taken. They are
disclosed because they influenced which tests are worth running. No test
statistic and no null distribution was computed.

- 10 zodiac signs survive (Pisces → Sagittarius; Capricorn and Aquarius are lost),
  each carrying 28–30 nymph labels: 294 label loci with legible text.
- 258 of those 294 label strings are distinct; the most repeated string occurs 5×.
- 292 paragraphs in the Recipes section (`$I=S`), 271 of them annotated in the
  transcription with the star drawn beside them (7 points ×154, 8 ×99, 6 ×7, 9 ×6).
- 872 paragraph-internal line-initial words are available in the same section as
  a within-section control.
- 54 pages carry both label loci and running-text loci (1,008 vs 8,641 tokens).

The 258/294 figure already rules out the simplest form of the numeral
hypothesis — a fixed set of ~30 names or numerals restarting in each sign — so
Z3's gate below is stated against that reading rather than discovered by it.

## Held-out splits

| test | FIT (rules may be adjusted here) | TEST (reported) |
|---|---|---|
| Z1, Z2, Z3, Z4 | Pisces, Aries, Taurus, Gemini, Cancer | Leo, Virgo, Libra, Scorpius, Sagittarius |
| R1, R2 | Recipes pages, odd folio number | Recipes pages, even folio number |
| L1 | pages with even folio number | pages with odd folio number |

Permutation tests use 10,000 draws and seed 408 unless stated.

---

## Z1 — Ordinal gradient inside a ring  *(primary numeral test)*

**Question.** In every written numeral system, neighbouring numbers share more
material than distant ones (`vigintiquinque` / `vigintisex`; `xxv` / `xxvi`;
`twenty-five` / `twenty-six`). Do the nymph labels behave that way around a ring?

**Statistic.** Labels are converted to glyph-unit sequences. For every ring with
≥ 8 labels, all pairs are scored with normalised LCS similarity, and the pair is
tagged with its gap `g` in manuscript ring order.
- `Δ = mean sim(g=1) − mean sim(g≥3)`, pooled over rings, weighted by pair count.
- `ρ̄` = mean per-ring Spearman correlation between `g` and similarity.

**Null.** 10,000 permutations of label order within each ring (the label set is
held fixed; only positions move). Two-sided p.

**Power calibration.** The identical procedure is run on eight numeral series
1–30 (English, Latin, Italian, German, French, Roman, Greek Milesian,
`d`+Roman) cut into rings of exactly the observed ring sizes, and on three
negative controls (30 Culpeper herb headings; 30 random Voynich herbal-section
label words; 30 random Latin Vulgate types).

**Gate Z1.** The labels are called ordinal-like only if, on the TEST signs,
(i) permutation p < 0.01, **and** (ii) `Δ` ≥ 25 % of the median `Δ` over the
numeral controls at matched ring sizes. The report must state the fraction of
numeral controls that themselves clear p < 0.01 at these ring sizes — the test's
measured power. If that fraction is below 0.5 the test is declared underpowered
and no conclusion is drawn in either direction.

## Z2 — Same slot across signs

**Question.** If the numbering restarts in each sign, label *k* of Leo should
resemble label *k* of Virgo.

**Slot conventions**, all three reported, all fixed here:
A. index within sign, manuscript order;
B. index within ring, rings aligned outer-first across signs;
C. clock position rounded to the nearest 30 minutes.

**Statistic.** mean similarity of same-slot cross-sign pairs − mean similarity of
different-slot cross-sign pairs. **Null.** 10,000 within-sign slot permutations.

**Gate Z2.** p < 0.01 on TEST signs under at least one convention **and** effect
≥ 25 % of the numeral controls' effect under the same convention.

## Z3 — Inventory

**Statistic.** distinct label strings / total; number of strings shared by ≥ 2
signs; distinct glyph units in labels vs. in running text on the same pages;
label type-token ratio against 1,000 length-matched resamples of running-text
words.

**Gate Z3.** "Fixed inventory" (a repeated set of names or numerals) is asserted
only if distinct/total < 0.5. Reconnaissance puts it at 0.878, so this gate is
expected to fail; it is recorded so that the number is reported against a stated
threshold rather than interpreted after the fact.

## Z4 — Positional morphology

**Statistic.** Mutual information between position and form:
positions = {rank block 1–10 / 11–20 / 21–30 within sign} × {thirds of the ring},
forms = {first glyph unit} × {last glyph unit}. Four combinations.
**Null.** 10,000 permutations of rank within sign / within ring.
**Gate Z4.** Any MI with permutation p < 0.01 after Bonferroni over the four
combinations is reported as positional structure. Otherwise: none.

---

## R1 — The paragraph opener: word or ornament?

Medieval recipe collections open every entry with the same word (*Recipe*,
*Item*, *Take*). Voynich paragraphs open with a gallows character. Three
sub-tests decide between "opening word" and "decorated initial".

Primary stratum: Recipes pages in Currier language B (f103r–f116r). Pages f58r/v
(language A) are an out-of-sample check.

**(a) Gallows rate.** Share of paragraph-initial words beginning with a gallows
(`t p k f cth ckh cph cfh`), against the same share among the 872 paragraph-
internal line-initial words and among all Recipes words. Permutation null.

**(b) Ornament test.** Strip the leading gallows from each paragraph-initial
word and ask whether the residue is attested elsewhere in the section as a free
word. Compared against the same operation applied to gallows-initial words drawn
from non-paragraph-initial positions, matched on the specific gallows character
and on word length. 10,000 resamples.

**(c) Lexical-opener test.** Top-1 and top-5 type share, and entropy, of the
paragraph-initial words and of their stripped residues, against the matched
control.

**Gate R1.**
- *Ornamental initial* is asserted if (b) shows the residue attested at a rate
  indistinguishable from or above the matched control (two-sided p > 0.05) **and**
  (a) exceeds the control by ≥ 3 SD.
- *Lexical opener* is asserted only if one word type, or one stripped-residue
  type, accounts for ≥ 10 % of paragraph openers with permutation p < 0.01 —
  the rate a real *Item* / *Take* formula produces.
- Both gates may fail. That is a reportable outcome, not a null result to bury.

## R2 — Do the drawn stars index the text?

For the 271 star-annotated paragraphs: do point count (7 vs 8), *dotted* and
*tail* predict (i) the opening word's first glyph unit, (ii) paragraph length in
words, (iii) the presence of any of the 50 most frequent Recipes types?
**Null.** 10,000 permutations of the star annotations over paragraphs;
Bonferroni over the 53 tests.
**Gate R2.** Report anything surviving Bonferroni p < 0.01. Registered
expectation: nothing survives.

## L1 — Label register vs. running text

**Question.** Labels name things; running text has grammar. If a set of word
endings is common in text and rare on labels, those endings are grammatical
material rather than part of the name — the split that has to exist before any
vocabulary work.

**Design.** Within-page only (same scribe, same Currier language, same section,
so those three confounds are removed by construction). Words are matched on
glyph-unit length; each label word is compared only against text words of the
same length on the same page.

**Statistic.** For the 25 most frequent word-final glyph units (K = 25, frozen):
within-page log-odds ratio label vs. text, pooled Mantel–Haenszel style.
**Null.** 10,000 permutations reassigning the label/text tag within page among
length-matched words.

**Positive control.** Culpeper's *Complete Herbal*: entry headings (herb names)
vs. entry bodies, same statistic, same matching, at character level.

**Gate L1.** A name/grammar split is asserted if ≥ 3 units show |log-odds| ≥ 1
with permutation p < 0.01 after Bonferroni over K = 25, **and** the pooled effect
is ≥ 25 % of the Culpeper control's. The report lists the units on each side.

---

## Replication

Every gate that passes on ZL3b is re-run on GC2a-n (an independent
transcription). A gate that passes on one transcription and fails on the other
is reported as transcription-dependent and is not claimed.

## What would count as meaning

- Z1 or Z2 passing → the labels are a counting system; the recurring
  morphemes are the numerals. This would be the first read units in the book.
- R1 *ornamental* passing → the first character of a Voynich paragraph carries no
  lexical content; every word list and every entropy figure computed over
  paragraph-initial words in the literature is measuring an ornament. Minor, but
  it changes what the openers are.
- R1 *lexical* passing → the manuscript has an entry formula, and the Recipes
  section is a list of entries.
- L1 passing → a stated, testable split of every word into name-part and
  grammar-part.
- Everything failing → reported as failing, with the measured power of each test,
  so the next pass knows which probes were too weak rather than which were tried.
