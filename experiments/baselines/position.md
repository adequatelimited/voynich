# Locus-position and repetition baselines

First-token lengths and adjacent repetition on P0 loci are compared to 39 within-locus token shuffles for each normalization variant.

Status: **actually executed; descriptive seed; zero competitive points**. Python 3.14 standard library; seed 408. The local protocol was frozen after an engineering smoke run had already inspected the join variant. It is not independent preregistration. No search for a best variant occurred; all join, split and strict runs are published.

Reproduce the complete suite with the commands in [the harness guide](../../tools/research/README.md). Exact source hashes, code hashes, commands, elapsed/CPU time and raw outputs are in [the protocol](../../protocols/launch-seed-v1.json), [comparison](../comparisons/launch-seed-v1.json) and referenced run manifests.

| Variant | Retained paragraph tokens | Mean encoded token length | Conditional bits/symbol | Section NMI | Source-hand NMI |
|---|---:|---:|---:|---:|---:|
| join | 32,514 | 5.37003 | 2.14573 | 0.26446 | 0.41520 |
| split | 34,977 | 4.99282 | 2.12253 | 0.20171 | 0.31929 |
| strict | 29,791 | 5.20449 | 2.07874 | 0.31677 | 0.38596 |

This common table locates the result within the shared sensitivity study; each file's output pointer identifies its actual full diagnostics. Conditional entropy is a plug-in estimator within tokens at matched symbol count, not the whole-corpus average or a translation score.

## join

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184558-358352Z-9b662cb7/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184558-358352Z-9b662cb7/output.json), JSON member `position`.

The retained scope contains 3,881 P0 loci of at least two tokens. The first-token minus nonfirst-token mean length is 0.56035 encoded symbols; adjacent repeat rate is 0.008765. The raw 39 shuffle values and finite tail diagnostic are included; no corrected significance or causal conclusion is asserted.

## split

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184600-812043Z-129fed73/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184600-812043Z-129fed73/output.json), JSON member `position`.

The retained scope contains 3,882 P0 loci of at least two tokens. The first-token minus nonfirst-token mean length is 0.52526 encoded symbols; adjacent repeat rate is 0.009133. The raw 39 shuffle values and finite tail diagnostic are included; no corrected significance or causal conclusion is asserted.

## strict

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184603-376651Z-72d40bae/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184603-376651Z-72d40bae/output.json), JSON member `position`.

The retained scope contains 3,865 P0 loci of at least two tokens. The first-token minus nonfirst-token mean length is 0.45304 encoded symbols; adjacent repeat rate is 0.009930. The raw 39 shuffle values and finite tail diagnostic are included; no corrected significance or causal conclusion is asserted.

## Limits and next evidence

EVA encodes shapes: its characters, apostrophes and atomic rare-symbol codes are analytical units, not recovered graphemes or phonemes. Unreadable/unsupported tokens are excluded; join and split select the first source alternative, while strict excludes ambiguous tokens. Drawing interruptions become apparent spaces. Subtype P0 loci need not equal physical manuscript lines.

The English comparison is a fixed prefix of one prose work; authored and copied/mutated controls test limited failure modes, not the space of all languages or historical mechanisms. Clustering uses one fixed initialization and source-specific metadata with strong potential quire/section/hand dependence. No independent human reproduction, image-based corpus validation or external scholarly endorsement is claimed.
