# H004-C: cross-transcription STA-family local-order screen

Status: **frozen before H004-C outcome evaluation**

Protocol version: `H004-C-v1`

## Claim boundary

H004-C asks whether the same physical-locus/component events show excess
preceding-context STA-family similarity in ZL, GC, and the outcome-unexamined
IT third witness, relative to a joint matched static-order null.

A pass would establish only that H004's transcriptional order effect survives
a third historical transliteration under this alignment and family-distance
rule. It would not establish linguistic words, copying, an edit operation, a
generator, sound, meaning, or translation. ZL, GC, and IT are correlated views
of one manuscript and share IVTFF/STA conversion infrastructure; they are not
independent corpus samples.

The IT file has already been downloaded, byte-pinned, parsed for integrity, and
sampled at the header/format level. No H004 event projection, target/context
comparison, or effect outcome has been computed or inspected. Before any such
evaluation, persist a discovery manifest containing this exact protocol, the
input and specification hashes, every ZL/GC skeleton position, every frozen
target and ordered context, every exclusion/reset reason, and the ZL/GC-stage
results. Record the manifest hash. Thereafter no alignment, target, threshold,
or exclusion rule may change.

## Inputs and inherited constants

- ZL STA1 SHA-256:
  `8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a`.
- GC STA1 level-0 SHA-256:
  `b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3`.
- IT STA1 SHA-256:
  `215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4`.
- Reuse H004's whole-page rule
  `SHA256("H004-v1:" + page_id)[0] < 51`, ten-component window, and page-equal
  primary aggregation.

## Frozen ZL/GC skeleton

Use position IDs `(page_id, locus_number, component_ordinal)`.

1. Restrict to H004 reserved pages and `P*` loci. Align loci only by exact
   `(page_id, locus_number)`.
2. Require both ZL and GC loci to exist, have valid non-`!` locators and generic
   type `P`, and have matching known `$I`, `$L`, and `$H`. Any failure is a hard
   gap.
3. Convert each locus into ordered certain-boundary slots. Treat `.`, `<->`,
   and `<~>` as boundaries; do not split commas. Remove comments/metadata and
   flatten only syntactically valid ligature braces. Retain invalid slots in
   the ordinal count.
4. Mark a slot invalid if it contains an uncertain space, alternative, `?`,
   `Z1`, malformed STA codes or ligatures, or any residue.
5. Admit a locus only when ZL and GC have exactly the same slot count. Align
   slots strictly by ordinal; never use string similarity or edit distance to
   choose an alignment.
6. Missing or unequal loci, invalid slots, page boundaries, either witness's
   paragraph boundary, any paragraph-boundary disagreement, or an `$I/$L/$H`
   change resets the run. Freeze paragraph-initial status only where ZL and GC
   agree; otherwise reset and exclude the disputed position.
7. The unit is an ordinal transliteration component, not a demonstrated word
   or manuscript glyph.

Within each shared run, freeze a target only when it has exactly the ten
immediately preceding shared valid positions. Record its exact ordered context
IDs, page, agreed `$I/$L/$H`, agreed paragraph-initial status, and locus-relative
position (`singleton`, `first`, `middle`, or `last`). Never slide or substitute
a predecessor later.

## Frozen IT projection

For every frozen locus, require the same IT locus key, a valid `P*` locator,
matching known `$I/$L/$H`, and exactly the frozen component count. Map by
ordinal only. Missing/count-mismatched loci are hard gaps. IT-invalid slots,
paragraph boundaries, metadata mismatches, and paragraph-status disagreement
reset the final three-witness run.

A frozen event is IT-evaluable only if its target and all ten exact predecessor
IDs remain valid in one final three-witness run. If any slot fails, discard the
event and record the attrition reason by page and Currier variety. Never add a
target that becomes possible only in IT or replace a failed predecessor.

## STA-family distance

For each valid component, parse consecutive two-character STA1 codes, exclude
`Z1`, and replace each code by its first uppercase family letter while
preserving order and repetitions.

Use ordinary unit-cost Levenshtein distance on family strings: insertion,
deletion, and substitution each cost one; there are no transpositions,
normalization, weights, or post-hoc equivalences. Cap only after computation
into `0`, `1`, or `>1`.

For each witness and frozen event, compute the minimum distance from its target
to the same ten predecessor position IDs. Co-primary metrics are `C` (minimum
at most one) and `U` (minimum exactly one); exact repetition `E` is diagnostic.
Distance one is one edit between STA-family strings, not a demonstrated scribal
or manuscript-glyph edit.

## Joint matched null

Shuffle aligned witness tuples jointly, never witnesses independently. At the
ZL/GC stage the object is `(ZL_family, GC_family)`; after projection it is
`(ZL_family, GC_family, IT_family)`.

Shuffle only within
`page × I × L × H × family-length-vector × paragraph-initial × line-position`
cells. The length vector contains both witness lengths before projection and
all three afterward. This preserves each page's exact aligned tuple multiset,
each witness's length/layout distribution, cross-transcriber dependence, and
the run/target/context skeleton while destroying assignment to local order.
Initialize each pool in skeleton-position order and apply the same Fisher-Yates
permutation to the whole tuple.

Generate 9,999 joint permutations per stage. Seeds are the unsigned big-endian
integer from the first 16 SHA-256 bytes of
`H004-C-v1|ZG|seed=4004` and `H004-C-v1|ZGI|seed=4004` respectively.

For each witness and metric, report the within-page then page-equal observed
rate, null mean, delta, empirical quantiles, one-sided Monte Carlo
`p = (1 + count(null >= observed)) / 10000`, and page residual signs against
each page's permutation mean. Report target-weighted Currier A/B rates as in
H004. Never pool witness p-values or treat witness-event triples as independent.

## Pre-IT ZL/GC gate

Do not run the IT event projection unless the frozen ZL/GC skeleton has at least
30 reserved pages and 1,500 targets, at least five pages and 200 targets in
each Currier variety, and at least 80% of targets in cells containing more than
one distinct ZL/GC tuple.

For both `C` and `U`, ZL and GC must each have delta at least 0.02, one-sided
`p <= 0.005`, and positive page residuals on more than 60% of pages. For both
metrics in each witness and each Currier A/B stratum, require positive delta
and `p <= 0.025`.

Failure rejects H004 as a ZL/GC-robust STA-family route and leaves the IT event
projection unrun. It does not erase H004-A's ZL-EVA descriptive result.

## Post-IT validity and advancement gates

Validity requires at least 30 final shared pages and 1,500 events; at least five
pages and 200 events in each Currier variety; at least 80% of frozen ZL/GC
events surviving overall and separately in A/B; at least 80% of final targets
in cells with more than one distinct triple; and all tuple-multiset,
run, target-ID, and context-ID invariants passing.

On the final IT-eligible subset, recomputed ZL and GC deltas for `C` and `U`
must remain positive with positive residuals on more than half the pages.
Failure means IT eligibility changed the estimand and is inconclusive.

Advance only the narrow third-witness robustness claim if validity passes and
IT has, for both `C` and `U`, delta at least 0.02, one-sided `p <= 0.005`, and
positive page residuals on more than 60% of pages. Separately in A and B, both
IT metrics must have positive delta and `p <= 0.025`. Pairwise page-sign
agreement and IT-minus-ZL/GC residual differences are diagnostics only. `E`
remains diagnostic.

## Rejection and inconclusive rules

For each IT co-primary metric, define `q05` as the 500th smallest of 9,999 null
statistics and the favorable useful-margin bound as `B = observed_IT - q05`.
If post-IT validity passes and `B < 0.02` for either metric, reject H004 as a
transcription-robust near-edit route under H004-C.

If advancement fails but neither metric excludes the margin, or if alignment,
attrition, breadth, or permutation validity fails, the result is inconclusive.
Never retune the alignment, window, family mapping, distance, cells, margins,
or thresholds after IT projection. Even a full H004-C pass leaves H004-B's
Markov-surrogate test mandatory before any copy/edit-mechanism claim.
