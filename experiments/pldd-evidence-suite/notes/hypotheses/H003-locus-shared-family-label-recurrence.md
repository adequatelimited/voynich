# H003: cross-transcriber locus-shared family-level label recurrence

Status: **retrospective advancement criterion not met**

## Motivation

H002's two held-out exact-EVA matches failed independent GC glyph-member agreement but retained the same STA family sequences. This may reflect allography, or it may merely make the matching rule looser. H003 was designed after H002 was inspected and retrospectively screens the family-level route across the corpus rather than rescuing the two examples by assertion.

## Claim

True-label STA family sequences present in both ZL3b and GC2a at the same aligned locus should recur in locus-shared prose type sets on the same page more often than on peer pages. A positive result would prioritize family sequences for blinded image work; it would not establish positional word agreement, allography, or meaning.

## Frozen protocol

- Inputs: pinned `sta1/ZL3b.txt` and `sta1/GC2a_0.txt`.
- Align loci by `(page_id, locus_number)`; exclude locator `!` and loci absent from either witness.
- In each locus, accept only components bounded by certain spaces. Exclude uncertain spaces, alternative readings, unreadable/unknown `Z1`, and malformed components.
- Convert each accepted STA word to its family sequence by retaining the first character of each two-character STA code.
- Locus-shared label/prose types are unordered set intersections of the ZL and GC family sequences in the aligned locus. This is co-presence, not positional word alignment. Do not count a form present in only one witness.
- Label subtypes: `La`, `Lc`, `Lf`, `Ln`, `Lp`, `Ls`, `Lt`, `Lz`. Prose: `P*`.
- Strata and peer null: same illustration `$I`, Currier `$L`, and hand `$H`, own page excluded, within the same retrospective partition.
- Partition by whole page using SHA-256 of `H003-v1:<page_id>`; first byte below 64 enters partition B (25%). This partition was defined after H002 output was inspected. Partition B is not an untouched holdout; all six of its pages had already appeared in H002 discovery material.
- Frozen advancement criterion: partition-B enrichment above zero, at least five partition-B pages with peers, at least 30 evaluated label types, and positive scores on more partition-B pages than negative scores.
- Report both partitions and the minimum-breadth checks. Crossing those minima is not a statistical power analysis.

## Interpretation boundary

Family-level matching is less specific than member-level matching. Even a positive result must beat a matched family-frequency null and survive visual adjudication before it can inform translation. No family sequence receives a gloss in this test.

## Result

- Partition A: 20 pages with peers, 215 label-family types, 48 local hits versus 43.0649 expected; enrichment 2.30%. Page scores: 11 positive, 4 zero, 5 negative.
- Partition B: 6 pages with peers, 62 label-family types, 15 local hits versus 13.5 expected; enrichment 2.42%. Page scores: 2 positive, 1 zero, 3 negative.
- The minimum breadth, label-count, and aggregate direction checks passed. The frozen page-sign check failed because negative partition-B pages outnumbered positive pages.

Disposition: the frozen advancement criterion was not met; do not advance this route as a crib. This retrospective test does not establish absence of family-level recurrence. No family sequence receives a gloss.
