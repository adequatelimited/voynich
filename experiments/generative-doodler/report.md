# The doodler test: can a content-free process fake the Voynich fingerprint?

## In plain words

Imagine a medieval artist doodling fake writing to make his drawings look scientific. He
isn't writing a language — he just has habits: favorite ways to start words, favorite
middles, favorite endings, and he keeps riffing on whatever he wrote a minute ago.

We built three robot doodlers that do exactly that — no dictionary, no meaning, just
habits — and let each one "write" a full fake Voynich manuscript. Then we compared the
fakes with the real text.

**What the robots faked easily:** how often words repeat, how rich the vocabulary is, and
the general look of the letter soup. So "someone was just improvising pretty gibberish"
is genuinely possible — a doodler *can* look like the Voynich at first glance.

**What they couldn't fake:** the real manuscript is oddly *disciplined*. Word endings are
more predictable, the letter patterns are more constrained, and common words get reused
far more deliberately than casual improvisation produces. Whatever the scribe was doing,
it followed stricter rules than free doodling — whether those rules encoded a real
language or just a very systematic art project is exactly the question still open.

One more curiosity: if the robot only copies-and-slightly-changes recent words, it invents
way too many new words. To sound like the real manuscript it must deliberately reuse its
old favorites — meaning the real scribe had a stable working "vocabulary", real or
pretend. Nobody doodles that consistently by accident.

**Bottom line:** "they were just having fun" survives round one, but the fun was
surprisingly rule-bound. The next tests (fake scribes with stricter word templates,
and checking whether star labels match their pictures) will narrow it further.

*Technical details follow.*

---

**Experiment date:** 2026-09-06 · **Corpus:** `data/corpora/ZL3b-n.txt` (repo-pinned, sha256 `bf5b6d4a…`, IVTFF comments stripped) · **Code:** `doodler.py` (stdlib-only, seed 1904)

## Question

A plausible hypothesis of artistic play: the scribe(s) drew imaginary plants and wrote a
realistic-looking script *as illustration* — inventing words on the fly from a fixed set of
script habits, riffing on what they had just written, with meaning (if any) only in the
moment. If such a **content-free** process reproduces the corpus' quantitative fingerprint,
then "the text encodes linguistic content" loses its remaining statistical support
(Lloyd's argument). If it cannot, the residue tells us where real structure lives.

## Models (all content-free)

| Model | Mechanism |
|---|---|
| **M0 random** | Uniform letters, empirical word lengths. Sanity null. |
| **M1 syllable table** | Rugg/grille analogue: words assembled from a small fixed syllable table with biased cell usage. |
| **M2 self-citation** | Schinner-style: invent from a fixed char-bigram "habit" set, or copy a recent word with a small context-consistent mutation, plus Simon-style preferential verbatim reuse of established types. |

## Results (32,238 tokens each)

| Metric | Corpus | M0 | M1 | M2 (best) |
|---|---|---|---|---|
| type/token ratio | **0.288** | 0.963 | 0.785 | **0.304** ✓ |
| char H1 (bits) | **4.01** | 4.93 | 4.06 | **3.93** ≈ |
| conditional bigram entropy H2\|1 | **2.24** | 4.89 | 2.94 | 2.75 ✗ |
| Zipf slope (log-log, ranks 10–1000) | **−1.06** | −0.60 | −0.68 | −0.76 ✗ |
| word length mean | **5.61** | 5.60 | 6.65 | 4.69 ✗ |
| word-final char entropy | **2.56** | 5.09 | 2.93 | 2.91 ✗ |
| Heaps ratio (types@50% / total) | **0.59** | — | — | 0.55 ≈ |

Best M2 setting: `p_new=0.05–0.2 (insensitive), recency=0.5, preferential-verbatim=0.4`.

## Findings

1. **The coarse fingerprint is reproducible without content.** Type/token ratio, unigram
   entropy and approximate vocabulary-growth all land near corpus values using nothing but
   script habits + self-citation + preferential reuse. The "artist doodling structured
   pseudo-words" hypothesis is quantitatively viable at this level.

2. **Three properties resist our doodler.** The manuscript has (a) lower conditional bigram
   entropy (2.24 vs 2.75 achievable here), (b) more predictable word endings (final-char
   entropy 2.56 vs 2.91), and (c) a steeper Zipf slope (−1.06 vs −0.76). A scribe
   improvising purely from habit + recent memory, as parameterized, is *less* constrained
   than the real text.

3. **A diagnostic surprise:** with copy-and-mute dominant, type diversity *explodes*
   (ttr 0.76 at low invention rates) — every mutation mints a new type. Matching the corpus
   requires that ~40% of tokens be verbatim reuse of already-established types via
   preferential attachment. Whatever produced the text recycled its "vocabulary" far more
   deliberately than naive improvisation does.

## Interpretation

The content-free hypothesis survives round one but does not close the case. The residual —
tight word endings, deeper frequency law, lower entropy — is exactly where a real encoding
*or* a more disciplined production rule (e.g., a fixed word-grammar template the scribe
followed, a grille with stronger column structure, or multi-session dialect drift) would
hide. Both readings remain open; the pilot narrows where to look.

## Limitations

- Single corpus (ZL3b), single seed, composite distance is a heuristic; parameter grid is coarse.
- The M2 "habit set" is derived from corpus bigrams — content-free but not corpus-free;
  this biases toward fitting char-level stats, so the misses at (2) are *despite* that advantage.
- Line-level phenomena (line-initial glyph effects, paragraph structure) and the Currier
  A/B section split are not yet modeled; foldout/label text is included in the corpus.
- This is an informative pilot, not a replication of Schinner (2007) or Rugg (2004);
  differences from their published results are not assessed here.

## Next steps

- Constrain the habit generator with a word-grammar template (prefix–core–suffix slots)
  to test whether property (b) falls; grid the grille (M1) column-bias strength for (c).
- Multi-session variant: drift the habit weights mid-stream and test for an emergent
  Currier A/B split against per-section corpus stats.
- Label consistency probe: zodiac star labels vs. depicted features (tests the
  "few stably meaningful words" variant of the hypothesis).
- Multi-seed runs with confidence intervals; repeat against GC2a for transcription robustness.

## Reproduce

```sh
python doodler.py --corpus ../../data/corpora/ZL3b-n.txt --out results/ --seed 1904
```
