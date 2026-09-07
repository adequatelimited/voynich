# Adversarial critique of the generative-falsification family — results

**Protocol:** [PROTOCOL.md](PROTOCOL.md), committed before the script ran (commit `15b6999`).
**Script:** `adversarial_critique.py`. **Output:** `results/results.json`, `results/stdout.txt`,
`results/source_hashes.json`. **Run record:** `experiments/runs/2026-09-07T013500Z-adversarial-critique/`.

The critic's job here was to damage the family's claims (PRs #3–#9), not to add another
model. Every verdict below is the label the frozen rule selected. Post-hoc observations are
marked as such and change no verdict.

## Verdicts by the frozen rules

| Rule | Target claim | Verdict |
|---|---|---|
| R0.1 | All headline numbers (10,120 types, ttr 0.289, H2\|1 2.26, final-glyph H 2.58, 30 % page-private) | **CONTAMINATED** — the shared parser leaves IVTFF mark-up inside tokens; 2,454 of the 10,120 types (24 %) are artefacts |
| R0.2 | "Richest vocabulary of all at equal size" | **RICHEST SURVIVES** — by 108 types over Latin (7,252 vs 7,144 at 35k tokens) under the primary treatment of uncertain spaces; by 1,602 under the family's treatment |
| R1.1 | "No language approaches the letter-pair constraint" | **ALPHABET-ROBUST** — 0.80 bits below the lowest language after glyph merging and identical determinism merging |
| R1.2 | "No language approaches the final-glyph entropy" | **ALPHABET-DEPENDENT** — gap to Finnish is 0.27 bits if `iin/in/ii/ee` are letter sequences, 0.08 bits if they are single glyphs |
| R2.1 | "The residue is what device models cannot yet fake" | **NOT REPRODUCED BY TESTED CIPHERS** (frozen) — but see the post-hoc note: the only failed gate for the plain verbose cipher of Latin is a type-ratio bound calibrated to the contaminated count |
| R3.1 | "Neighbouring pages share 2× more vocabulary: topical organisation is measurable fact" | **LANGUAGE/SECTION ARTEFACT** — within the same Currier language and section the ratio is 1.14, not 2 |
| R3.2 | "30 % page-private vocabulary, ten times a real encyclopedia" | **HAPAX-RICHNESS CONSEQUENCE** — decontaminated share 19.3 %, of which 16.6 points are what random page assignment gives for this hapax profile |
| R4.1 | "Richest vocabulary — odd for language" (medieval-orthography control) | **SURVIVES this control** — Middle English Chaucer reaches only ttr 0.137; but see R0.2: Latin and Finnish already sit at 0.204/0.203 against the manuscript's 0.207 |

## The critic's memo: problems found by reading the family's code

1. **One parser, shared by every pilot, is contaminated.** `load_pages()` strips only `<!…>`
   comments. Paragraph markers `<%>`/`<$>` lose their brackets and stay glued to words
   (`%tchedy`, `daiin$`: 736 + 736 tokens); `[a:b]` alternative readings are kept verbatim
   (`d[o:a]r`, 775 tokens); `<->` gap markers glue two words into one (`dar-shol`, 669
   tokens); illegible `?` is deleted so `d?n` becomes the new type `dn`; `@nnn;` extended
   glyphs leave fragments. 2,830 tokens and 2,454 types are affected. The doodlers were
   fitted to this target and their corpus-derived habit sets learned the junk characters.
2. **The treatment of uncertain spaces decides the vocabulary claim.** IVTFF `,` marks a
   space the transcriber was unsure about. The family silently merged across it. Treated as
   a space, the manuscript has 7,252 types at 35k tokens; merged, 8,746. Latin has 7,144.
3. **Model selection and evaluation use the same metrics.** Each pilot grid-searches its
   parameters to minimise a composite distance on the headline metrics and then reports how
   many of those metrics the best point "matches". No held-out metric and no held-out text
   were ever used. "Matched" is therefore an optimistic statement in every pilot.
4. **Distant-page sampling crosses languages and sections.** "Distant" meant any page more
   than 20 folios away, so the comparison pairs mostly straddle the Currier A/B split and the
   section boundaries. The adjacency effect was measured against the wrong baseline.
5. **Controls were not size-matched.** Culpeper's entry-private share (2.8 %) comes from
   242,234 tokens in 138 entries of ~1,750 words; the manuscript figure from 35,000 tokens in
   226 pages of ~170 words. The English tokeniser also drops one-letter words while the
   Voynich tokeniser keeps them.
6. **Labels were pooled with paragraph text.** 880 label, radial and circular loci were
   counted as page text. (Effect turned out small: see A3.)
7. **The probability judgments (50 → 60 → 65 → 55 %) are narrative.** They are not derived
   from any likelihood and moved with each pilot's story. The two live branches — device and
   ciphered content — were "compatible with both" under every metric, and the family never
   built the strongest case for the content side.

## A0 — Parser contamination

| Parser | tokens | types | ttr | hapax/types | H2\|1 | final H | word len | adj J | dist J | page-private |
|---|---|---|---|---|---|---|---|---|---|---|
| family (as published) | 34,986 | 10,120 | 0.289 | 0.758 | 2.261 | 2.585 | 5.60 | 0.080 | 0.042 | 0.302 |
| clean, `,` = space (primary) | 38,184 | 7,734 | 0.203 | 0.683 | 2.132 | 2.523 | 4.96 | 0.109 | 0.063 | 0.193 |
| clean, `,` = no space | 35,492 | 8,804 | 0.248 | 0.717 | 2.147 | 2.457 | 5.34 | 0.090 | 0.049 | 0.238 |

Same-tokeniser richness at 35,000 tokens (Unicode letters only, one-letter words kept):

| Corpus | types | ttr | hapax/types |
|---|---|---|---|
| Voynich clean, `,` = space | **7,252** | 0.207 | 0.682 |
| Voynich clean, `,` = no space | 8,746 | 0.250 | 0.717 |
| Latin (Vulgate) | 7,144 | 0.204 | 0.597 |
| Finnish | 7,100 | 0.203 | 0.576 |
| Russian | 5,945 | 0.170 | 0.570 |
| Italian | 4,396 | 0.126 | 0.529 |
| Greek | 4,286 | 0.123 | 0.527 |
| Spanish | 3,832 | 0.110 | 0.526 |
| German / French / Culpeper | 3,558 / 3,550 / 3,548 | 0.10 | 0.46–0.50 |
| English (WEB) | 2,505 | 0.072 | 0.419 |

What survives: the manuscript's *hapax share* (68–72 % of types) is well above every
language (≤ 60 %). That is the sharper way to state the vocabulary anomaly; the type count
itself is a near tie with Latin.

## A1 — Alphabet confound

Manuscript H2|1 and final-symbol entropy by alphabet level (clean, `,` = space):

| Level | symbols | H2\|1 | final H |
|---|---|---|---|
| (a) raw EVA | 25 | 2.132 | 2.523 |
| (a) + determinism merge (`qo`) | 26 | 2.162 | 2.531 |
| (b) benched gallows + `ch`/`sh` | 31 | 2.255 | 2.526 |
| (b) + determinism merge | 32 | **2.291** | 2.535 |
| (c) (b) + `iiin iin in ii eee ee` | 37 | 2.398 | **2.711** |
| (c) + determinism merge | 38 | 2.441 | 2.719 |

Languages after the identical determinism merge (which fired only on `qu` and German `ch`):
Greek 3.089, German 3.172, Italian 3.166, English 3.188, Spanish 3.205, Culpeper 3.243,
French 3.252, Finnish 3.246, Latin 3.337, Russian 3.465. Lowest raw final-letter entropy:
Finnish 2.794, Italian 2.970, Greek 3.230, Latin 3.300.

R1.1: gap 0.80 bits (2.291 vs Greek 3.089) — **ALPHABET-ROBUST**. Even at level (c) with
merging, the gap is 0.65 bits. This is the family's one residue that survives everything.

R1.2: level (c) final entropy 2.711 vs Finnish 2.794 — gap 0.083 — **ALPHABET-DEPENDENT**.
Honest reading: the family's "2.58 vs nearest 2.80" was computed with `$` glued to 736
word endings; the clean value is 2.52 at letter level and 2.71 if the i-groups are single
glyphs. The anomaly is between 0.27 and 0.08 bits depending on a glyph-identity assumption
the family never stated. Note also that level (c) gives the manuscript more symbols than any
language's letters, which favours this verdict; the protocol accepted that asymmetry.

## A2 — Advocate for the content side

Untuned ciphers built by frequency-rank assignment from the clean manuscript (the same
corpus-derived advantage the doodlers had). Gates: H2|1 ≤ 2.56, final H ≤ 2.90,
0.22 ≤ ttr ≤ 0.32.

| Plaintext / cipher | types | ttr | H2\|1 | H2\|1 det | final H | word len | page-private |
|---|---|---|---|---|---|---|---|
| Culpeper plain | 3,263 | 0.093 | 3.219 | 3.219 | 3.578 | 4.45 | 0.124 |
| C2 verbose fixed | 3,263 | 0.093 ✗ | **2.280 ✓** | 2.449 | **2.612 ✓** | 9.38 | 0.124 |
| C3 verbose homophonic | 16,224 | 0.464 ✗ | 2.660 ✗ | 2.722 | 3.177 ✗ | 10.2 | 0.525 |
| C4 abbreviated homophonic | 11,847 | 0.339 ✗ | 2.615 ✗ | 2.667 | 3.115 ✗ | 7.33 | 0.377 |
| C5 positional | 3,255 | 0.093 ✗ | 2.689 ✗ | 2.689 | 1.575 ✓ | 7.00 | 0.124 |
| Latin plain | 7,132 | 0.205 | 3.323 | 3.337 | 3.301 | 5.32 | 0.176 |
| **C2 verbose fixed** | 7,132 | **0.205** ✗ (gate 0.22) | **2.312 ✓** | 2.528 | **2.782 ✓** | 11.1 | 0.176 |
| C3 verbose homophonic | 21,660 | 0.621 ✗ | 2.658 ✗ | 2.720 | 3.152 ✗ | 12.2 | 0.591 |
| C4 abbreviated homophonic | 15,196 | 0.436 ✗ | 2.591 ✗ | 2.679 | 3.009 ✗ | 7.60 | 0.402 |
| C5 positional | 7,109 | 0.204 ✗ | 2.819 ✗ | 2.819 | 1.657 ✓ | 7.76 | 0.175 |
| *C6 abbreviated fixed (exploratory, post hoc)* | 5,352 | 0.154 | 2.162 | 2.289 | 2.635 | 7.04 | 0.129 |

C1 (monoalphabetic) reproduced every plaintext statistic exactly, as a sanity check requires.

R2.1: **NOT REPRODUCED BY TESTED CIPHERS** by the frozen rule.

**Post-hoc note, changes no verdict.** The ttr gate [0.22, 0.32] was written around the
family's 0.289 and a pre-run estimate of 0.264. The corrected manuscript ttr at 35k tokens
is 0.207 (`,` = space) or 0.250 (`,` = no space). The plain verbose cipher of Latin has ttr
0.205, H2|1 2.31 and final entropy 2.78: it sits inside the two entropy gates and within
0.003 of the corrected manuscript ttr. Its visible failure is word length (11.1 vs 4.9),
which the protocol deliberately did not gate. The exploratory C6 (drop non-initial vowels,
then fixed verbose) brings length to 7.0 and H2|1 to 2.16 at the cost of ttr (0.154). A
cipher between C6 and C4 would presumably hit both — that is the tuning game the doodlers
played and the critic refuses to play. The proper follow-up is a fresh pre-registration
with corrected gates that include word length (see "Next").

Component-wise, the claim that the residue "cannot be faked" is already false for two of
its three parts: an untuned verbose cipher of a real text reproduces both entropy residues.

## A3 — Structure claims

Clean corpus, `,` = space; 200 token permutations across pages preserving page sizes.

| Quantity | observed | null mean ± sd | null 97.5 % |
|---|---|---|---|
| adjacent Jaccard | 0.1093 | 0.1045 ± 0.0013 | 0.1070 |
| distant Jaccard (> 20 folios) | 0.0625 | 0.0915 ± 0.0011 | 0.0939 |
| page-private share | 0.1932 | 0.1661 ± 0.0021 | 0.1709 |

Decomposition of the "2×" contrast: adjacent pages are 4.6 % above their shuffle null;
distant pages are 32 % *below* theirs. The contrast comes from distant pages being
dissimilar across the A/B and section blocks, not from neighbours being similar.

| Pair class | pairs | Jaccard |
|---|---|---|
| adjacent, same Currier language and same section | 178 | 0.120 |
| adjacent, different language or section | 47 | 0.068 |
| adjacent, different language | 30 | 0.051 |
| distant (≥ 5 folios), same language and section | 197 | 0.1055 |
| **within-class ratio** | | **1.137** |

Sensitivities: paragraph loci only (206 pages) 0.111 / 0.064 / 0.186 — labels did not
matter. `,` = no space: observed 0.090 / 0.049 / 0.238 vs null 0.086 / 0.075 / 0.205,
within-class ratio 1.141 — same picture.

R3.1: **LANGUAGE/SECTION ARTEFACT.** A real but small adjacency effect exists (3.7 sd above
the null; +14 % within a block). It is not "2×" and it is not evidence of encyclopedia
structure specifically: a scribe filling consecutive pages from a slowly drifting habit
would produce the same. R3.2: **HAPAX-RICHNESS CONSEQUENCE**: 30.2 % → 19.3 % after
decontamination, of which 16.6 points are expected from random page assignment; the excess
is 2.7 points (gate 5). R3.3: with Culpeper truncated to 35k tokens its entry-private share
is 12.5 %, so the ratio is 1.55, not 10 — and that comparison is still confounded by entry
size (17 entries of ~2,000 words vs 226 pages of ~170).

## A4 — Medieval orthography

| Text (35k tokens) | types | ttr | hapax/types | H2\|1 | final H |
|---|---|---|---|---|---|
| Chaucer, Skeat (Middle English spelling) | 4,793 | 0.137 | 0.531 | 3.161 | 3.552 |
| Chaucer, Purves (modernised spelling) | 4,644 | 0.133 | 0.544 | 3.188 | 3.662 |
| Voynich clean (`,` = space) | 7,252 | 0.207 | 0.682 | 2.137 | 2.518 |

R4.1: **SURVIVES this control** (0.137 ≤ 0.22). Orthography effect +0.004 — negligible
here, with a caveat: Skeat regularised spelling toward the Ellesmere manuscript, so this is
a weaker test than a diplomatic transcription would give. The stronger blow to "odd for
language" came from A0: Latin and Finnish are within 1.5 % of the corrected type count.

## Where the family's claims stand after this critique

- **Letter-pair constraint (H2|1):** the one solid residue. Robust to alphabet and to
  every control. But an untuned verbose cipher of a real text reaches it, so it separates
  "text with fixed glyph groups" from "plain language", not device from cipher.
- **Final-glyph predictability:** weakened; size 0.08–0.27 bits depending on glyph identity;
  reproduced by verbose ciphers.
- **Vocabulary richness:** numbers must be restated; the type count is a near tie with
  Latin; the hapax share (68–72 %) is the form of the anomaly that survives.
- **Encyclopedia structure:** withdrawn as stated; a +14 % within-block adjacency effect
  remains, compatible with drift.
- **30 % page-private:** withdrawn; 19 % observed, 17 % expected from richness alone.
- **Probability judgments:** unsupported before, unsupported now. The honest statement is
  that under this metric family "strict device" and "verbose-ciphered real text" remain
  observationally equivalent, and the critic's untuned cipher got as close to the fingerprint
  as the family's tuned devices on the entropy residues.

## Deviations from the protocol (recorded)

1. First run crashed in the confound block (page-dict lookup); fixed before any number was
   read.
2. First complete run used a Latin-only tokeniser for the languages, which silently emptied
   Greek and Russian (H2|1 0.65 and 0.25). Fixed to Unicode letters after the junk values
   were seen; R1.1 changed from a meaningless "dependent" to **ALPHABET-ROBUST**.
3. R0.2 was first computed on 38,184 Voynich tokens; corrected to the protocol's ≤ 35,000.
4. Purves' editorial note blocks leaked into the modernised-Chaucer sample (ttr 0.153);
   removed in two iterations (0.131, then 0.133). Affects only R4.2, which has no gate.
5. The R2.1 ttr gate was calibrated to the contaminated count; reported as frozen, with the
   post-hoc note above. C6 was added after the fact and is excluded from R2.1.
6. Added sensitivities not in the protocol: `,` = no-space null and confounds; family-parser
   page metrics for comparison.

## Next (proposed, not executed)

1. Restate every family number with the clean parser and both uncertain-space treatments,
   then re-run M2/M4/M5 against the clean target — with a held-out half of the pages.
2. Pre-register A2′: corrected gates (ttr within ± 0.03 of the clean value under the same
   `,` treatment; H2|1 ≤ 2.45; final H ≤ 2.80; word length within ± 1.0; Zipf within ± 0.15),
   cipher families fixed in advance, plaintexts Latin and an abbreviated medieval Latin
   herbal. Any hit ends the device-vs-cipher story under these metrics.
3. The discriminating test the family keeps postponing: meaning-driven similarity. Two
   pages depicting similar plants (independent illustration classification) should share
   more vocabulary than drift predicts if the text is about the pictures; a device predicts
   no such effect beyond adjacency.

## Reproduction

```
python adversarial_critique.py --repo ../.. --lab <dir with bibles/, pg49513.txt, pg22120_chaucer_skeat_CT.txt, pg2383_chaucer_purves.txt> --out results/
```

Stdlib only; deterministic. Input hashes in `results/source_hashes.json`. Chaucer texts:
Project Gutenberg 22120 (Skeat, *Chaucer's Works* vol. IV) and 2383 (Purves), fetched
2026-09-07, public domain in the USA, not redistributed here.
