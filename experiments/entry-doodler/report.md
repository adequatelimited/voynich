# The encyclopedia doodler: faking the Voynich as a book of per-page entries

## In plain words

**IDEA** (proposed by the dataset host, an artist)
- The manuscript is not a "book-book" (a story you read front to back).
- It is an illustrated encyclopedia: each page is a separate entry about its own picture
  (a plant, a star, a recipe).
- The text may still be decorative — but if so, the artist faked *entry structure*, not just words.

**TEST METHOD**
- First we measured the real manuscript like an encyclopedia: do neighboring pages share
  vocabulary (same topic)? Does each page have private words for its own subject?
- Then we built a robot encyclopedia-writer: every page gets a small set of invented
  "topic words", most of which carry over (slightly mutated) to the next page; within a
  page, words are reused preferentially, sometimes mutated, sometimes brand-new.
  No dictionary, no meaning, page layout copied from the real manuscript.

**REAL MANUSCRIPT MEASUREMENTS**
- Neighboring pages share **2× more vocabulary than distant pages** (0.080 vs 0.042) —
  the text is topically ordered, like a reference work.
- **30% of each page's word types appear on that page only** — every page has private
  vocabulary for its own subject.

**ACTUAL RESULT (best robot: carry=0.3, topic=60, prime=2, reuse=0.6)**
- Page structure: **matched**. Neighbor-sharing 0.075 (real 0.080), distant-sharing 0.035
  (real 0.042), page-private vocabulary 28% (real 30%).
- Vocabulary size: close — 8,600 word types vs 10,120 real.
- Still not matched: letter-pattern constraint (H2|1: 2.91 vs 2.26), word popularity curve
  (−0.64 vs −1.05), word length (4.4 vs 5.6 chars).

**SO IT IS "THIS"**
- "It is organized like an encyclopedia" — **confirmed by the data, ~90%** (this part is
  no longer a hypothesis; the topical page structure is measurable fact).
- "A methodical artist faking an encyclopedia" — **still strong, ~50%**: our content-free
  robot *can* fake the encyclopedia structure itself.
- "Real encyclopedia content" — **still alive, ~35%**: the same fine-grained discipline as
  in pilot 1 remains unexplained by doodling.
- "Pure formless fun" — **~15%**, downgraded again: the manuscript's organization is
  too deliberate for that.

*Percentages are informal judgments from two pilots, not computed probabilities.*

---

## Technical summary

**Pilot 2 in the generative-falsification family**, extending `outcome-generative-doodler-pilot`.

- Corpus: `data/corpora/ZL3b-n.txt` (repo-pinned; page-level IVTFF parse, comments stripped).
- Real page-structure measurements (new): adjacent-page Jaccard 0.0804, distant 0.0422
  (sampled, seed 7), page-unique type share 0.3024 over 226 pages.
- Model M3: per-page topic vocabularies, carry-over with mutation between pages
  (`carry`), topic priming (`prime`), within-page preferential reuse (`reuse`),
  mutation and fresh habit-driven invention. Char habits = corpus bigrams
  (content-free but not corpus-free, as in pilot 1).
- 24-parameter grid, seed 408. Best `carry=0.3, topic=60, prime=2, reuse=0.6, mut=0.1`.

| Metric | Real | M3 best | Match |
|---|---|---|---|
| types | 10,120 | 8,603 | ≈ |
| type/token | 0.289 | 0.246 | ≈ |
| adjacent-page Jaccard | 0.080 | 0.075 | ✓ |
| distant-page Jaccard | 0.042 | 0.035 | ✓ |
| page-unique share | 0.302 | 0.279 | ✓ |
| H2\|1 (bits) | 2.26 | 2.91 | ✗ |
| Zipf slope | −1.05 | −0.64 | ✗ |
| word length | 5.6 | 4.4 | ✗ |

## Findings

1. **The manuscript is measurably encyclopedia-structured.** Topical page ordering and
   page-private vocabulary are quantitative facts, independent of any hypothesis.
2. **That structure is itself fakeable content-free.** M3 reproduces all three page-level
   metrics with no lexicon or meaning — page topics that carry over and drift suffice.
3. **The same fine residue persists across both pilots:** character-level constraint
   (H2|1, word endings), the steep frequency law, and word length survive every
   content-free parameterization tried so far. The unexplained structure is at the
   *word-grammar* level, not the document level.
4. **Diagnostic, mirroring pilot 1:** without carry-over, entry models under-share
   vocabulary across pages; with mutation-driven copying only, they over-invent types.
   The real text balances deliberate reuse with slow topical drift.

## Interpretation

The "fake encyclopedia by a methodical artist" hypothesis is viable at both the document
level (this pilot) and the coarse text level (pilot 1). Both pilots leave the identical
unexplained residue: a strict word-internal grammar. That is now the sharp question —
either it is a fixed decorative template, or it is where real content hides. A
template-constrained doodler (prefix–core–suffix slots) is the discriminating next step.

## Limitations

- Single corpus (ZL3b), single seed, heuristic composite distance; page-order effects of
  foldouts are not specially handled (adjacent "pages" inside foldout scans inflate
  neighbor similarity slightly in both real and model data).
- M3's habit set is corpus-derived, as in pilot 1; misses occur despite this advantage.
- `carry`/`topic` parameters are fitted, not derived from any paleographic evidence.
- The two pilots were not run against GC2a; transcription-robustness is untested.

## Next steps

- Template doodler (M4): word grammar slots with fixed inventory per slot; test whether
  H2|1, final-char entropy and Zipf all fall at once.
- Zodiac label-consistency probe: repeated depictions vs. repeated labels.
- Multi-seed confidence intervals; GC2a cross-check; Currier A/B section drift variant.

## Reproduce

```sh
python entry_doodler.py --corpus ../../data/corpora/ZL3b-n.txt --out results/ --seed 408
```
