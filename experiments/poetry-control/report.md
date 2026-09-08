# Poetry control: does rhyme explain the manuscript's word-ending discipline?

## In plain words

**IDEA** (control suggested by Vasily Gnuchev, 2026-09-07)
- The manuscript's strongest unfaked property is how predictable its word endings are
  (final-glyph entropy 2.59 bits).
- But poems — real language! — force word endings too: rhyme. Maybe the manuscript's
  endings are just versification-like discipline, not content or device?

**TEST METHOD**
- Measured line-final and word-final predictability in Shakespeare's Sonnets (strict
  rhyme, 154 sonnets — the most ending-constrained real genre we could pick) against the
  manuscript's real lines and against prose pseudo-lines (Culpeper, Alice).

**ACTUAL RESULT**

| Source | Final-glyph entropy, all words | …at line end | Top line-final words |
|---|---|---|---|
| **Voynich (real lines)** | **2.59** | 2.99 | daiin 1.7%, dy 1.1%, dam 0.8% |
| Sonnets (rhymed verse) | 3.70 | 3.50 | thee 2.1%, me 1.4%, be 1.0% |
| Culpeper (prose) | 3.64 | 3.64 | the 7.4%, and 5.3% |
| Alice (prose) | 3.59 | 3.61 | the 6.0%, and 3.6% |

**WHAT IT MEANS**
- Rhyme does NOT produce the manuscript's discipline. Even the rhyme position in sonnets
  (3.50 bits) is far less constrained than *every word* in the manuscript (2.59 bits).
- Verse achieves its endings by recycling a few rhyming words (thee/me/be); the manuscript
  achieves far tighter endings across a 10,000-word vocabulary — a different mechanism.
- The final-glyph residue survives its hardest real-language control. Versification is
  excluded as an explanation.
- Side observation: the manuscript's line endings are slightly *less* constrained than its
  average word (2.99 vs 2.59) — the opposite of rhyme. Whatever the line unit is in the
  manuscript, it is not a rhyme line.

**SO IT IS "THIS" (judgment unchanged, evidence stronger)** — strict system/device ~55%,
encoded content ~35%, plain language ~8%, formless fun ~2%. The two surviving residual
properties (letter-level constraint, word endings) have now also withstood the verse
comparison.

*Percentages: informal judgment, not measurement.*

---

## Technical summary

**Poetry control in the generative-falsification family.** Line-structured metrics over
the pinned corpus' real lines (IVTFF loci), the Sonnets' real lines, and prose
pseudo-lines at the Voynich mean line length (7 words). Line-final word's final-char
entropy: Voynich 2.99, sonnets 3.50, prose 3.61–3.64. All-word final-char entropy:
Voynich 2.59, sonnets 3.70, prose 3.59–3.64. Line-initial first-char entropy: Voynich
3.13, sonnets 3.84, prose 4.08–4.10. The manuscript's line-initial position is also
mildly constrained relative to real genres.

## Limitations

- One verse corpus (English sonnets); medieval/Latin verse (e.g., hymn metre, rhymed
  Latin) may behave differently — a medieval verse control is a fair next step.
- English rhyme is phonetic; a syllabic or template verse (e.g., troubadour forms) could
  constrain endings harder.
- Device models (M5b) currently generate no line structure; their line metrics are
  unmeasured — a line-aware generator is required before device-vs-manuscript line
  comparison.

## Reproduce

```sh
python poetry_control.py --corpus ../../data/corpora/ZL3b-n.txt \
  --sonnets ../../data/corpora/pg1041.txt --culpeper ../../data/corpora/pg49513.txt \
  --alice ../../data/corpora/pg11.txt --out results/
```
