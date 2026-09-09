# H005: pharmaceutical-fragment to whole-herbal referential anchors

Status: **frozen before any target-prose retrieval outcome**

Protocol version: `H005-v1`

## Claim boundary

H005 asks whether a label attached to a pharmaceutical herb fragment retrieves
the whole-herbal page that a pre-existing visual-source claim identifies as the
same or a similar depicted plant. This is the first semantic screen in the
repository: the external claim fixes a depicted referent before the label is
compared with target prose.

A pass would license only the low-confidence referential gloss
`same depicted plant/entity as whole-herbal folio X`. It would not identify a
species, sound, language, grammar, cipher, or fluent translation. The q15/q19
claims are research-page assertions rather than a peer-reviewed botanical gold
standard. A species or genus gloss additionally requires blinded agreement by
two independent botanical experts on a historically attested taxon and a
successful unseen-image prediction.

No target-page prose overlap, retrieval rank, or model outcome was inspected
before this protocol and the complete source-anchor manifest were frozen. Query
labels and their transcription feasibility were inspected to define a
fail-closed benchmark; those are not semantic outcomes.

## Frozen evidence and claim universe

- Source claims: the complete current fragment-to-whole-herbal statements on
  <https://voynich.nu/q15/index.html> and
  <https://voynich.nu/q19/index.html>, retrieved 2026-07-10. Their retrieved
  HTML byte hashes, page update dates, and the exact 35-claim ledger are in
  `data/derived/h005-source-anchor-manifest.json`, frozen at SHA-256
  `f6f6f8edd9b21f5aa1e952e26a6104ad327a15a98e426a1fc4ed8e735b9631c7`.
  The copyrighted HTML is not redistributed locally.
- Images: Yale MS 408 IIIF Presentation manifest, SHA-256
  `c1f12b6ad256b91e1b5c8015c2107de1c2ff24e573f4524c53e8f4004bccfc23`.
- EVA source: ZL3b-n SHA-256
  `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`.
- STA1 ZL source SHA-256:
  `8438ba1c45f47fe1d06b5262cbcdf60ce69158a0edbd4dd802612896f3217e2a`.
- STA1 GC level-0 source SHA-256:
  `b39cabbd9c8c8a098bfa9f76e0649291d17d77e1cb4fb0a3351ff7bdc832ace3`.
- Reserved IT STA1 source SHA-256:
  `215f2d05690828c00bd4ae00d6201df31050adcd81601343b142ae91b9dfeee4`.

The source inclusion rule is mechanical: include every explicit q15/q19
statement that a numbered pharmaceutical fragment appears to be the same plant
as, shows some similarity with, or was observed by Petersen to resemble a
named whole-herbal folio. Exclude taxon guesses, container comparisons, and
whole-herbal-to-whole-herbal claims. Deduplicate only by pharmaceutical page,
fragment number, and target page. Keep failures and conflicts.

Only exact coordinate-mapped `Lf` loci are plant-fragment queries. Never use
`Lc` container labels. The manifest records nine current claims with no `Lf`
and one unresolved f101v item-188 mapping; those are ineligible in v1 and may
not be replaced. One f99v item-110 query is predeclared as two loci and counts
as one query, not two chances. Legacy ZL comment claims that are absent from or
conflict with the current q15/q19 pages remain recorded but excluded.

## Strict ZL/GC query gate

Map STA1 loci only by exact `(page_id, locus_number)`. Convert certain-boundary
components with the frozen H004-C `sta_family_slots` rule: dot and drawing
breaks delimit slots; comments are inert; valid ligatures are flattened;
uncertain spaces, alternatives, unreadable glyphs, `Z1`, malformed codes, and
residue invalidate a slot without guessing.

Admit a source pair only if every predeclared `Lf` locus exists in both ZL and
GC, is type `Lf` in each, has the same nonzero component count, every component
is valid, and ZL and GC yield exactly the same ordered STA-family strings.
There are no preferred alternatives, fuzzy query alignments, or partial
multi-locus admissions. Record every exclusion reason.

## Physical-folio holdout

Derive a physical folio by stripping side and panel suffixes from the target
page, for example `f90r2 -> f90`. A target physical folio is held out exactly
when

`first_byte(SHA256("H005-v1:" + physical_folio_id)) < 51`.

All recto, verso, and panel targets from one physical folio share the split.
Never rehash, replace, or move a failed pair. The frozen strict holdout is
expected to contain f19, f43, f44, f48, and f57, one target claim on each except
that f48 has two source claims before query attrition. H005 must stop as
inconclusive if fewer than five strict held-out pairs on five physical folios
remain.

## Candidate documents

For each query, candidates are all ZL/GC pages with `$I=H`, at least one valid
`P*` STA-family component, and the same known target-page Currier `$L` and LFD
hand `$H`. Use prose loci only; never search labels or comments. Build separate
ZL and GC documents using identical page membership and scoring parameters.
The query string is the ordered multiset of its strict consensus family tokens.

Freeze two retrieval models:

1. `M0`: exact STA-family-token BM25 with `k1=1.2`, `b=0.75`, and
   `idf = log(1 + (N - df + 0.5)/(df + 0.5))`.
2. `M1`: boundary-marked STA-family character 2- and 3-gram BM25 with the same
   constants. For each token, add `^token$` before extracting n-grams; do not
   generate n-grams across token boundaries.

For each model and witness, score every candidate page. Rank descending with
midranks for ties. A pair's conservative rank is the worse of its ZL and GC
ranks; its conservative reciprocal rank is the reciprocal of that worse rank.
Select exactly one model by discovery-set mean conservative reciprocal rank,
breaking ties in favor of `M0`. Lock the model automatically before evaluating
the holdout. Report both models on discovery as multiplicity diagnostics, but
only the locked model is primary on holdout.

## Matched null

Use 9,999 deterministic replicates seeded by the unsigned big-endian integer
from the first 16 SHA-256 bytes of `H005-v1|target-null|seed=5005`.

In each replicate, group queries sharing one claimed target page. Within each
target `(Currier, hand)` stratum, map those unique target groups without
replacement to candidate herbal pages in the same stratum; duplicate-target
queries stay together. Keep the original discovery/holdout query split. For
each replicate, repeat model selection on its reassigned discovery targets and
evaluate the selected model on its reassigned holdout targets. This null
therefore pays for model selection and preserves duplicate-target dependence,
candidate membership, query forms, page lengths, and the fixed split.

Report held-out MRR, top-3 fraction, null means and empirical quantiles, and
one-sided `p = (1 + count(null >= observed))/10000`. Also report results by
quire, source wording strength, and unique query form. For each quire with both
discovery and holdout coverage, use the globally selected model and require
observed-minus-matched-null mean MRR to be positive separately on discovery
and holdout; neither the observed run nor a null replicate may retune by quire.
A stable identical query form attached to visually distinct target components
kills a plant-identity gloss even if aggregate retrieval is favorable.

Before target scoring, the strict query inventory already identified one such
collision: `q15-f89r1-25-f57r` and `q19-f99v-95-f44r` have the same stable
query form while their claimed whole-herbal targets are visually distinct.
Keep this as a predeclared identity-gate failure; do not reinterpret the form as
a broader class after seeing retrieval results.

## Advancement, rejection, and IT reserve

The ZL/GC source-claim route advances only if all of these hold:

- at least 16 strict pairs over at least 12 physical target folios, at least
  three pharmaceutical pages, both q15 and q19, and the five-pair/five-folio
  held-out minimum;
- held-out conservative MRR exceeds the selection-adjusted matched-null mean by
  at least 0.15;
- at least 60% of held-out pairs rank their target in the top three;
- the MRR and top-3 one-sided randomization p-values are each at most 0.01;
- observed-minus-null MRR is positive on both discovery and holdout separately
  in q15 and q19 wherever each subset has coverage; and
- no visually distinct-target collision invalidates a proposed identity form.

Do not project target prose through IT unless the ZL/GC gate passes. If it does,
rerun the locked model without retuning. Require at least 80% query/document
coverage and unchanged positive direction; IT is a correlated robustness view,
not an independent corpus.

Even a ZL/GC+IT pass is `promising`, not a gloss, until a text-blind image
benchmark contains at least 12 accepted pairs over 10 physical targets and
both quires. Image acceptance requires glyphs, folio identifiers, page numbers,
and surrounding layout to be masked; each fragment is shown with its claimed
whole herb plus nine feature-matched distractors in randomized order; at least
two of three annotators who have not seen the claim list must choose the claimed
target top-1 and the median `same copied exemplar` score must be at least 3/4.
Failures remain in the artifact.

If statistical advancement fails with valid breadth, reject the q15/q19
plant-label retrieval route under H005-v1. If breadth, mapping, image-gold, or
transcription coverage fails, call the affected layer inconclusive rather than
negative evidence about manuscript semantics. Never retune mappings, split,
models, null, thresholds, or confidence wording after target-prose evaluation.
