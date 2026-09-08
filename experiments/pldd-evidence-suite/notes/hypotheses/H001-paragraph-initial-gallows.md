# H001: paragraph-initial gallows enrichment

Status: **known structural feature reproduced on reserved ZL3b pages; semantic interpretation unassigned**

## Claim

Basic-EVA word candidates beginning with `k`, `t`, `p`, or `f` are enriched at transcriber-marked paragraph starts relative to noninitial positions. This tests a known positional feature. It does not assert that the forms are words, sounds, initials, headings, or instructions.

## Frozen evaluation

- Corpus: pinned ZL3b.
- Include only certain basic-EVA components; uncertain spaces/readings and extended codes are excluded with reasons.
- Split by whole page: SHA-256 of `H001-v1:<page_id>`; first byte below 51 is held out.
- Measure paragraph-initial rate, background rate, and smoothed log2 odds.
- Whole-token candidates are exploratory. A candidate passes the frozen directional screen only if it has an observed held-out initial occurrence and positive held-out log2 odds; smoothing alone cannot count.

## Result

- Discovery: 82.50% of eligible paragraph initials versus 5.25% of background positions; log2 odds 6.403.
- Held out: 92.96% versus 5.63%; log2 odds 7.723.
- Exploratory whole-token candidates: `tchedy`, `pchedy`, `tar`, `tol`.
- Only `tol` had an observed held-out paragraph-initial occurrence in this split. The others did not pass the directional screen. For `tol`, this is one initial occurrence among six held-out occurrences and is descriptive rather than confirmatory.

This positional feature was previously reported in the literature, including Currier's analysis: <https://www.voynich.nu/extra/img/curr_main.pdf>. The present result is a same-manuscript, same-transcription reproduction with a reserved-page check, not an independent replication.

Disposition: retain the leading-gallows feature as a hard positional constraint. Assign no gloss. Future mechanisms must explain why the feature survives reserved pages and why it is position-sensitive.

Generated evidence: `results/baseline-zl3b.json` and `results/baseline-zl3b.md`.
