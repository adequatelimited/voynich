# H004-B: discovery-trained Markov surrogate screen

Status: **retracted before implementation or outcome inspection; do not run**

Protocol version: `H004-B-v1`

## Retraction record

No H004-B result was generated or inspected. An independent pre-execution
audit found that the proposed greedy without-replacement sampler is not a draw
from a Markov model conditioned on fixed cell multisets: it weights the next
draw without accounting for the likelihood of future transitions. Its hard
zero/backoff rule could also starve reserved-only candidates until late in a
run, and its support diagnostic would not reliably expose that bias. The
already-inspected H004-A page partition is additionally not a fresh holdout for
this follow-up.

This file is retained as an audit record, but H004-B-v1 must not be implemented
or cited as a valid Markov comparator. A replacement must use either a genuine
conditional sampler with positive support and frozen convergence gates or an
explicitly narrower predictive comparator, and must label the reused H004-A
partition retrospective.

All protocol text below this retraction record is historical and superseded by
`H004B2-contextual-comparator.md`.

## Claim boundary

H004-A found local near-edit ordering relative to a static matched permutation
null. H004-B asks whether that same ordering remains larger than a predeclared
useful margin when compared with order-1 and order-2 word-Markov surrogates
trained only on nonreserved pages.

Passing H004-B would establish only that the tested fitted Markov comparators do
not reproduce the measured local near-edit ordering. It would not identify
copying, establish a copy/edit generator, assign language or sound, or produce
a translation. Failure may reject H004 as a copy/edit-mechanism route without
implying that the manuscript has no other sequential structure.

## Fixed corpus and split

- Reuse H004-A's pinned ZL3b input, certain basic-EVA eligibility rules,
  `SHA256("H004-v1:" + page_id)` whole-page split, sequence resets, ten-token
  context, 33 reserved evaluation pages, and 2,072 reserved targets unchanged.
- Train on every valid run on nonreserved pages, including short runs and pages
  with fewer than ten H004 targets. Do not use reserved tokens to fit counts.
- Train Currier A and B separately. Exclude unknown Currier strata and never
  back off across Currier varieties.
- Prefix each training run with distinct `<BOS2>, <BOS1>` sentinels. For each
  Currier variety count unigrams `c_L(w)`, order-1 transitions `c_L(h1,w)`,
  and order-2 transitions `c_L(h2,h1,w)`. Do not count across run boundaries.
  Do not model EOS because reserved run lengths are fixed.

## Fixed page-cell-conditioned sampler

Each complete surrogate corpus preserves every reserved page's exact token
multiset within every existing H004 cell
`(I, L, H, EVA_length, paragraph_initial, line_position)`, as well as the exact
run skeleton, run lengths, target locations, and context locations. Only the
assignment of tokens to positions within those pools changes.

Traverse pages in document order, runs and positions in source order, and
candidate token types in lexical order. At each position, candidates are only
the token types still present in that position's exact page-cell pool.

- Order 1 weights candidate `w` by
  `remaining_multiplicity(w) * c_L(h1,w)`.
- Order 2 first weights candidate `w` by
  `remaining_multiplicity(w) * c_L(h2,h1,w)`.
- Order-2 hard backoff is order 2, then order 1, then Currier unigram, then
  uniform remaining multiplicity. Order-1 hard backoff is order 1, then
  Currier unigram, then uniform remaining multiplicity.
- Move down exactly one or more levels only when the total candidate weight at
  the current level is zero. Do not smooth, relax a cell, borrow another
  Currier variety, or add discovery-only vocabulary.
- Draw with integer cumulative weights and `randrange(total_weight)`. Remove
  one occurrence after selection. Reset generated history to the BOS sentinels
  at every run boundary.
- Assert for every surrogate that all pools empty exactly and that page-cell
  multisets, run lengths, target counts, context locations, and stratum
  skeletons match the observed reserved corpus.

## Randomness

Generate 9,999 complete surrogate corpora per model order. The master seed is
4004. Each model's independent deterministic seed is
`int.from_bytes(SHA256("H004-B-v1|order=N|seed=4004")[:16], "big")`, with
`N` equal to 1 or 2.

## Metrics

Reuse H004-A's metrics without alteration:

- `C`: within-page rate at which minimum Levenshtein distance to the preceding
  ten tokens is at most one;
- `U`: within-page rate at which that minimum is exactly one;
- exact-repeat rate as a diagnostic only.

The primary statistic is the mean of within-page rates with pages weighted
equally. For every model-order and metric combination report the observed
value, surrogate mean, observed-minus-surrogate delta, empirical quantiles,
one-sided Monte Carlo
`p = (1 + count(surrogate >= observed)) / 10000`, and page-specific residual
signs relative to each page's surrogate mean. Report the existing
target-weighted Currier A and B rates separately.

Also report sampler backoff proportions for all generated positions and for
evaluated target positions, separated by model order and Currier variety. A
position's recorded level is the first level with positive total weight before
the draw.

## Comparator-validity gate

All conditions are mandatory:

1. H004-A's static matched-null gate was met and every sampler invariant passes.
2. Uniform fallback is at most 1% of evaluated target positions for each model
   and each Currier variety.
3. Requested-order support at evaluated target positions is at least 50% for
   order 1 and at least 10% for order 2, separately in Currier A and B.

An invalid comparator is inconclusive and cannot count as evidence for either
advancement or rejection.

## Advancement gate

Advance only the statement that the two fitted Markov comparators did not
reproduce the effect if every condition holds:

1. In all four co-primary comparisons (`C` and `U` for orders 1 and 2), delta
   is at least 0.02, one-sided `p <= 0.001`, and more than 60% of reserved pages
   have positive residuals.
2. In all eight Currier comparisons (`C` and `U` by orders 1 and 2 by A/B),
   delta is positive and one-sided `p <= 0.00625`.
3. Both comparator-validity gates pass.

## Rejection and inconclusive rules

For each valid model-metric comparison, define the 95% upper useful-effect
bound as `observed - q0.05(surrogate statistic)`, where `q0.05` is the empirical
5th percentile. If this bound is below 0.02 for any co-primary comparison,
reject H004 as a copy/edit-mechanism route under this frozen metric: even a
favorable 5th-percentile surrogate leaves less than the predeclared useful
margin.

If advancement fails but no valid comparison excludes that useful margin, the
result is inconclusive. Do not retune the window, edit threshold, cells,
backoff, split, or gate after inspection.
