# Corpus alignment and bounded hypothesis tests, H001–H007

This contribution brings an existing research workspace into the shared repository as a runnable evidence suite. It adds source-retaining IVTFF and STA1 comparison tools and records what several explicitly specified manuscript tests did and did not establish. No token has a validated semantic or phonetic gloss.

The scientific package is in [`experiments/pldd-evidence-suite`](../../experiments/pldd-evidence-suite/README.md). Its README, publication adaptation record, file inventory and verification record identify the exact files and commands. Manuscript inputs and frozen protocol documents retain their original bytes. Publication-only changes, including portable input paths and exclusion of an unfinished later study, are disclosed separately.

## Provenance and chronology

The source workspace records research and retrieval dates of 2026-07-09 and 2026-07-10. These are retained author-recorded dates, not independently authenticated timestamps. Protocol hashes bind the definitions to the submitted artifacts; they do not establish public preregistration. This publication package was prepared on 2026-09-08 UTC.

Primary evidence is Zandbergen–Landini ZL3b, Glen Claston GC2a, their named STA1 conversions, the historical IT2a conversion, and Yale's IIIF manifest. Different transcriptions are correlated readings of the same manuscript, not independent manuscript samples. Derived family representations must not be mistaken for reversible phonetic alphabets. Exact inputs, versions, source URLs and hashes are listed in the package provenance and inventory.

## Outcomes and completion boundaries

### 1. A source-retaining corpus and cross-transcription audit capability

The parser preserves the 411,671 ZL3b source bytes while exposing 227 page/panel records and 5,385 loci. It provides explicit uncertainty and exclusion handling, named analytical views and locus-based comparison of the supplied ZL/GC STA1 files. Tests and H002/H003/H004-C/H005 examples expose agreement, ambiguity and attrition instead of silently forcing convenient matches. The original source is returned verbatim; this is not a demonstrated arbitrary AST-to-transcription serializer.

This is an additional tested implementation and an auditable cross-transcription workflow. It does **not** repair `experiments/meaning-probes/meaning_lib.py`, implement v101-specific byte-pair merges, or reproduce the upstream meaning probes. Those are follow-up integration tasks. EVA-only analysis functions reject other alphabets. STA1 family comparison is used only within its declared rules, preserving the raw independent readings.

The package also includes a 213-canvas Yale index, keeping composite and partial-foldout labels explicit rather than guessing a one-to-one panel mapping. Yale images, the IIIF manifest and raw transliterations already available through the Artheon contribution are excluded from novelty claims. There is no new image-access claim or separate image-hosting credit request.

H001 reproduces known paragraph-position structure. H002 and H003 provide failed or insufficient label-recurrence checks and alignment examples. They are included as context and validation, without separate claims for rediscovering known gallows behavior or multiplying corpus-baseline credit.

### 2. P001: an edge inventory that does not discriminate morphology

The selected one-prefix/two-suffix inventory produced 69 productive recombinations among 123 unseen affixed test types, but ranked only 2,309th of 5,082 equal-cardinality controls, at the 54.58th percentile against a 95th-percentile gate. The selected edge-slot route is rejected as a discriminating morphology claim; no edge or core receives a gloss. The record discloses that calibration and test partitions were inspected in the same exploratory session. It is an informative controlled pilot, not a pristine held-out confirmation.

### 3. H004: local order under a static null, with the full robustness sequence

The static matched-permutation screen uses the preceding ten tokens and explicit page/layout/length strata. Across 33 reserved pages and 2,072 targets, exact-or-one-edit proximity increases by 0.0504 (`p = 0.0001`), and one-edit-without-exact by 0.0379 (`p = 0.0003`), using 9,999 permutations. The corrected movable-target count is 2,000/2,072; source statistics were retained after that correction.

The package includes the B-v1 design retraction, B-v2's failed validity gates and C's failed cross-transcription route. B-v2 is inconclusive because unknown-token mass is too high and predictive log lift is negative. C retains only 648 targets and fails both breadth and co-primary effect gates. Its already-exposed permutation results remain in the audit record, including the chronology of execution beyond the failed breadth gate. C did not load or project IT outcomes. The original static report is a historical stage; subsequent reports govern the completed sequence.

The result is a bounded transcriptional order effect and its limits. Neither language, copy/edit generation, nor an alternative causal mechanism is identified or refuted by this sequence.

### 4. H005: pharmaceutical labels against a fixed external correspondence ledger

A 35-claim q15/q19 ledger yields 17 exact-coordinate, ZL/GC-compatible label-to-herbal-folio pairs. The five held-out pairs have conservative MRR 0.33991087 versus selection-adjusted null 0.19643035 (`p = 0.0568`), with 2/5 targets in the top three (`p = 0.1592`). The held-out q19 direction is negative. The identical stable family `AQABBA` occurs in claims targeting distinct folios f44 and f57. Every statistical advancement check and the distinct-target identity gate fail.

This rejects the specified source-claim retrieval route. It is not evidence that the manuscript lacks meaningful labels, and it identifies no botanical species. The external visual correspondence claims are not blinded botanical ground truth. IT target prose was left unopened by this study. The ledger, rules, null construction, full results and failures are included together.

### 5. H006: two exact fixed-three-trit line-reset models fail a necessary condition

H006 expands two explicit component tables under fixed three-trit blocks and independent phase-zero reset on each eligible logical prose line. Of 919 exact ZL/IT-consensus discovery lines, the PAIR and OPTIONAL_E models respectively produce 598 and 593 non-divisibility contradictions. A single contradiction suffices to reject either exact model. The 266 held-out residues are not computed.

The rejection applies to those two component tables and that reset/block conjunction. It does not reject other component tables, paragraph or continuous resets, variable-length codes, historical homophony, or Matlach et al.'s entire proposal.

### 6. H007: published-key coverage and unique-decoding limits

The literal Naibbe author decoder passes all three supplied author controls. Applied with the fixed published table and declared tokenization to 2,341 discovery occurrences, the class observer records 495 uncovered, 82 bigram-ambiguous and 3 compound-ambiguous occurrences. Both exact gates fail; the table does not evaluate the 777 held-out occurrences. No manuscript plaintext, label stream or language score is released.

The table-only follow-up shows why adding arbitrary deleted-boundary closure cannot turn this route into a unique decoder: the 82 existing ambiguous bigram occurrences retain their alternatives. The recorded atomic codebook contains 18,947 distinct ciphertext strings; 14,648 also admit a distinct multi-atom decoding. This closure over-approximates shuffled-deck support and does not reject the exact randomized encoder with a fully specified deck history.

Naibbe is a modern Voynich-like construction. Greshko did not assert that this table is the manuscript's historical key. The contribution is a literal fixed-key coverage/ambiguity case study and reusable diagnostic, not a refutation of his general ciphertext-compatibility thesis.

Required citation: Michael A. Greshko (2025), *The Naibbe cipher: a substitution cipher that encrypts Latin and Italian as Voynich Manuscript-like ciphertext*, Cryptologia, [doi:10.1080/01611194.2025.2566408](https://doi.org/10.1080/01611194.2025.2566408).

## Bounded comparison with the shared repository

Comparison base: `b470c129462ca22845371ec9a57c84bccc24af25`. This is a review of the public family registry, source catalog, branch/task records and directly related reports, not an exhaustive literature novelty claim.

| Existing material | Overlap excluded; useful increment offered |
|---|---|
| `seed-corpus-parser`, `seed-baseline-integrity`, `seed-local-harness` | Raw corpus acquisition, routine baseline counts and generic run scaffolding are not new. The additional implementation, explicit source preservation and worked STA1 alignment/attrition checks are inspectable capabilities. |
| `family-ms408-data-access` | The Yale manifest, 213 scans and existing source links are already available. Conservative canvas mapping is supporting tooling, not another image-access outcome. |
| `seed-baseline-position`, `research/claims/copy-generation.json` | General repetition and copy-generation questions already exist. H004 adds the specified preceding-ten-token matched-null experiment and its complete contextual/cross-transcription failure sequence. |
| `family-generative-falsification-word-grammar-template`, `family-generative-falsification-discriminating-tests` | Grammar/segmentation and illustration-linked vocabulary have existing tests. P001's exhaustive equal-cardinality inventory control and H005's exact-coordinate label-retrieval experiment have different decision rules and completion boundaries. H005 is not the first plant-association experiment. |
| `family-generative-falsification-meaning-probes` | Label/register questions and the GC2a-tokenizer limitation are already documented. This package does not claim their meaning-probes results or a completed fix; it supplies separately checkable cross-transcription infrastructure and different bounded experiments. |
| `seed-direction-negative-control-atlas`, `seed-direction-decipherment-budget` | The general idea of a failure atlas or an exception budget is not new. H006 and H007 supply executed diagnostics for particular fixed constructions with explicit limits. |

Related public reports: [meaning probes](../../experiments/meaning-probes/REPORT.md), [discriminating tests](../../experiments/discriminating-tests/REPORT.md), [position baseline](../../experiments/baselines/position.md), and [Artheon provenance](../artheon-ms408-hosted-dataset/rights.md).

## Validation, AI assistance and limits

The package verification record contains the actual current commands, interpreter/dependency information, results and artifact comparisons. Local tests and rebuilds are ordinary submitted execution evidence. Separate AI agents reviewed packaging and claim boundaries; this is not independent human replication, a scientific peer review, or an authenticated external execution receipt.

AI assistance is disclosed as primarily generated. Earlier exact model/snapshot/settings were not retained in the source workspace and are unknown; the current preparation used Codex with GPT-6, with no immutable snapshot or effort setting claimed. The human contributor directed the work and authorized submission. No claim of line-by-line human verification is made.

The unfinished H008 design and Latin comparator files are outside this contribution. No H008 evaluation or previously sealed holdout stage is authorized or performed by publication. Source facts, transcriptions, derived structures and interpretation remain separate throughout. Rights and reuse conditions are specified in [rights.md](rights.md).
