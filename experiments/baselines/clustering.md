# Source-label association and confounded clustering baseline

Unsupervised encoded-symbol page clusters are compared with ZL section and hand annotations; global and within-quire permutations expose confounding limits.

Status: **actually executed; descriptive seed; zero competitive points**. Python 3.14 standard library; seed 408. The local protocol was frozen after an engineering smoke run had already inspected the join variant. It is not independent preregistration. No search for a best variant occurred; all join, split and strict runs are published.

Reproduce the complete suite with the commands in [the harness guide](../../tools/research/README.md). Exact source hashes, code hashes, commands, elapsed/CPU time and raw outputs are in [the protocol](../../protocols/launch-seed-v1.json), [comparison](../comparisons/launch-seed-v1.json) and referenced run manifests.

| Variant | Retained paragraph tokens | Mean encoded token length | Conditional bits/symbol | Section NMI | Source-hand NMI |
|---|---:|---:|---:|---:|---:|
| join | 32,514 | 5.37003 | 2.14573 | 0.26446 | 0.41520 |
| split | 34,977 | 4.99282 | 2.12253 | 0.20171 | 0.31929 |
| strict | 29,791 | 5.20449 | 2.07874 | 0.31677 | 0.38596 |

This common table locates the result within the shared sensitivity study; each file's output pointer identifies its actual full diagnostics. Conditional entropy is a plug-in estimator within tokens at matched symbol count, not the whole-corpus average or a translation score.

## join

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184558-358352Z-9b662cb7/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184558-358352Z-9b662cb7/output.json), JSON member `clustering`.

Clusters use 191 page units and k=6. Section NMI is 0.26446; the global-shuffle mean is 0.05100 and within-quire-shuffle mean 0.28636. Hand NMI uses 190 pages with a single ZL H label; 1 mixed/unknown cases are excluded.

## split

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184600-812043Z-129fed73/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184600-812043Z-129fed73/output.json), JSON member `clustering`.

Clusters use 192 page units and k=6. Section NMI is 0.20171; the global-shuffle mean is 0.05282 and within-quire-shuffle mean 0.21050. Hand NMI uses 191 pages with a single ZL H label; 1 mixed/unknown cases are excluded.

## strict

Full output: [experiments/runs/launch-seed-v1/2026-09-06T184603-376651Z-72d40bae/output.json](../../experiments/runs/launch-seed-v1/2026-09-06T184603-376651Z-72d40bae/output.json), JSON member `clustering`.

Clusters use 187 page units and k=6. Section NMI is 0.31677; the global-shuffle mean is 0.05438 and within-quire-shuffle mean 0.32523. Hand NMI uses 186 pages with a single ZL H label; 1 mixed/unknown cases are excluded.

## Limits and next evidence

EVA encodes shapes: its characters, apostrophes and atomic rare-symbol codes are analytical units, not recovered graphemes or phonemes. Unreadable/unsupported tokens are excluded; join and split select the first source alternative, while strict excludes ambiguous tokens. Drawing interruptions become apparent spaces. Subtype P0 loci need not equal physical manuscript lines.

The English comparison is a fixed prefix of one prose work; authored and copied/mutated controls test limited failure modes, not the space of all languages or historical mechanisms. Clustering uses one fixed initialization and source-specific metadata with strong potential quire/section/hand dependence. No independent human reproduction, image-based corpus validation or external scholarly endorsement is claimed.
