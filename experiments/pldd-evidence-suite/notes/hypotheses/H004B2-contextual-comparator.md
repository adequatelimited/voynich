# H004-B-v2: teacher-forced contextual comparator

Status: **executed under the frozen protocol; inconclusive because both comparators failed validity**

Protocol version: `H004-B-v2`

This protocol supersedes the retracted H004-B-v1 urn sampler. It is a
retrospective conditional model check on H004-A's already-opened reserved
partition, not an independent confirmation and not a free-running Markov
generator.

## Claim boundary

H004-B-v2 asks whether discovery-trained order-1 and order-2 word-transition
likelihoods reproduce H004-A's `C` and `U` rates after conditioning on each
target's observed ten-token history and exact page/layout-cell token
distribution.

A pass advances only: “these teacher-forced order-1 and order-2 contextual
comparators did not reproduce the effect.” It cannot rule out a free-running
Markov generator, higher-order dependencies, morphology, syntax, topic,
copying, or another mechanism. A failure can reject H004's `C`/`U` statistics
as discriminating evidence beyond this comparator; it cannot reject copying as
a possible cause. Nothing in H004-B-v2 assigns sound, meaning, or a gloss.

## Training and frozen smoothing

Reuse H004-A's pinned input, sequence construction, page split, 33 reserved
pages, 2,072 targets, and ten-token contexts. Train only on valid runs from
nonreserved pages, separately for Currier A and B, without crossing a run or
Currier boundary.

For each Currier variety, count surface output types on discovery pages first.
The model vocabulary `V_L` contains every type with discovery count at least
two plus `<UNK>`. Map discovery singletons and all reserved types outside
`V_L` to `<UNK>` for model counts/lookups. Retain actual reserved EVA strings
for edit-distance scoring. Prefix each training run with distinct `<BOS2>` and
`<BOS1>` histories; sentinels are not output types.

With mapped discovery counts and `T` output tokens, freeze:

```text
P0(u) = (c(u) + 1/2) / (T + |V_L|/2)

P1(u | h) = (c(h,u) + P0(u)) / (c(h) + 1)

P2(u | h2,h1) =
    (c(h2,h1,u) + P1(u | h1)) / (c(h2,h1) + 1)
```

All probabilities are positive. An unseen context reduces exactly to the
lower-order model. Do not alter the singleton threshold, smoothing, mapping,
or vocabulary after outcomes are inspected.

## Target-conditional distribution

For each reserved target `t`, let `q_t(w)` be the exact empirical surface-type
distribution in its existing H004 cell
`page × I × L × H × EVA_length × paragraph_initial × line_position`:

```text
q_t(w) = cell_multiplicity(w) / cell_size
```

This deliberately conditions on the complete reserved cell, including the
target occurrence. It is a matched conditional comparator, not leakage-free
lexical prediction.

Using the observed preceding history and mapping `phi`, define:

```text
lift_1,t(w) = P1(phi(w) | phi(h1)) / P0(phi(w))
lift_2,t(w) = P2(phi(w) | phi(h2),phi(h1)) / P0(phi(w))

R_N,t(w) = q_t(w) * lift_N,t(w)
           / sum_v(q_t(v) * lift_N,t(v))
```

The `P_N/P0` likelihood ratio is mandatory; multiplying `q_t` directly by
`P_N` would count global frequency twice. Histories remain observed and fixed;
the comparator neither recursively generates contexts nor preserves realized
page-cell counts.

## Metrics and conditional simulation

For each target, compute analytically under `R_N,t` the probability of:

- `C`: minimum EVA Levenshtein distance to its observed preceding ten tokens
  is at most one;
- `U`: that minimum is exactly one;
- exact repetition, diagnostic only.

Aggregate expected probabilities within page and then average pages equally.
Report target-weighted Currier A/B summaries separately.

Generate 9,999 independent teacher-forced replicate datasets per order. In
each replicate, independently draw one candidate for every target from its
fixed `R_N,t`; keep every observed ten-token context fixed. Candidate order is
lexical. Construct exact rational weights once per target, reduce them to
integer cumulative weights, and draw with `randrange(total_weight)`.

Operational execution guard, frozen before any H004-B-v2 outcome inspection:
the incremental common denominator and the final reduced total weight may each
be at most 4,096 bits. Exceeding either ceiling produces no H004-B-v2 result
and an inconclusive operational disposition. Never approximate, truncate, or
renormalize the rational weights to evade this ceiling. This guard is not a
scientific acceptance criterion; it prevents an impractical exact simulation
from silently becoming an approximate one.

The order-specific seed is exactly:

```python
int.from_bytes(
    sha256(
        f"H004-B-v2|teacher-forced|order={N}|seed=4004".encode("ascii")
    ).digest()[:16],
    "big",
)
```

For each statistic report analytic expectation, replicate mean, observed minus
analytic expectation, replicate tail area
`(1 + count(replicate >= observed)) / 10000`, and page residual signs against
analytic expectation. Call this a conditional Monte Carlo tail area, not a
confirmatory p-value.

Use nearest-rank quantiles on the 9,999 replicates: q01/q05/q50/q95/q99 are
the 100th/500th/5000th/9500th/9900th sorted values. Apply every gate to
unrounded values and round only rendered output.

## Comparator-validity gate

All conditions are mandatory:

1. Every candidate probability is finite, positive, and normalized within
   `1e-12`; all target, page, stratum, context, and source-hash invariants match
   H004-A.
2. At least 80% of evaluated targets, overall and separately in Currier A/B,
   belong to cells containing at least two distinct surface types.
3. Discovery context support covers at least 50% of evaluated targets for
   order 1 (`c(h1) > 0`) and at least 10% for order 2
   (`c(h2,h1) > 0`), overall and separately in A/B.
4. Baseline candidate mass mapped to `<UNK>`,
   `mean_t sum_{phi(w)=UNK} q_t(w)`, is at most 20%, overall and separately in
   A/B. Report reweighted `<UNK>` mass under each `R_N,t` diagnostically.
5. The contextual distribution predicts the actual reserved target better
   than its cell baseline: page-equal mean
   `log R_N,t(actual) - log q_t(actual)` is positive, more than half of page
   means are positive, and the target-weighted lift is positive separately in
   A and B.

A comparator failing any validity condition is inconclusive and cannot support
advancement or rejection.

## Advancement gate

Advance the narrow comparator-failure statement only if all four order ×
co-primary comparisons satisfy:

- observed minus analytic expectation at least 0.02;
- conditional tail area at most 0.001;
- positive page residuals on more than 60% of reserved pages.

For all eight order × metric × Currier comparisons, require positive delta,
tail area at most 0.00625, and positive residuals on more than half of the pages
containing that Currier variety. Both order-specific validity gates must pass.

## Rejection and inconclusive rules

For each valid co-primary comparison define the favorable 95% useful-effect
bound `D95 = observed - q05(replicate statistic)`. If `D95 < 0.02` for any
comparison, reject H004's `C`/`U` statistic as discriminating evidence beyond
this teacher-forced comparator. Do not reject copying/editing as a possible
cause.

If advancement fails but no valid comparison excludes the useful margin, the
result is inconclusive. Do not retune the model, thresholds, page cells,
history, edit distance, or gates. Even a pass leaves free-running Markov
generation as a separate unresolved experiment.

## Result

The exact production run used 9,999 replicates per order and seed 4004. Exact
integer totals peaked at 159 bits for order 1 and 163 bits for order 2, below
the frozen 4,096-bit operational ceiling. Runtime was 15.894 seconds.

Both comparators failed the mandatory validity gate:

- baseline candidate mass mapped to `<UNK>` was 21.88% overall and 28.88% in
  Currier A, above the 20% ceiling;
- page-equal predictive log lift was -1.0242 for order 1 and -1.3741 for order
  2; all 33 page means were negative, and the A/B target-weighted lifts were
  also negative.

For order 1, `C` had observed-minus-expected delta 0.0081 and conditional tail
area 0.2174, while `U` had delta 0.0572 and tail area 0.0001. For order 2,
`C` had delta 0.0109 and tail area 0.1379, while `U` had delta 0.0631 and tail
area 0.0001. These mixed metric outcomes cannot override comparator invalidity.

Disposition: **inconclusive**. Do not advance the narrow comparator-failure
statement and do not reject H004's `C`/`U` statistics from this test. This test
does not reject copying as a possible cause and does not test a free-running
Markov generator.

Generated evidence: `results/h004b2-contextual-comparator.json` and
`results/h004b2-contextual-comparator.md` (JSON SHA-256
`01d26e78676f938e010c1d21fd2ce627bf9192932c4dee2fe2bd21a078c381bf`).
