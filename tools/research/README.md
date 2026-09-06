# Local research loop

The seed harness executes five real manuscript analyses on pinned ZL3b data, with three declared uncertainty policies. It requires **Python 3.14**, uses the standard library, runs without network access or model credentials, and makes no publication or scoring decisions. The initial runs took about eight seconds total on the recorded Windows machine. All project launch seeds receive zero competitive points, with evidence-tier baselines pending official assessment.

From the repository root, these commands work in PowerShell and a POSIX shell. Pick a new output name for each explicitly disclosed research program; existing protocols/comparisons are not overwritten.

```sh
python -m unittest discover -s tests/research -v
python tools/research/research.py prepare --id my-baseline-v1 --output artifacts/local/my-baseline-v1/protocol.json
python tools/research/research.py run --protocol artifacts/local/my-baseline-v1/protocol.json --output artifacts/local/my-baseline-v1/runs
python tools/research/research.py compare --protocol artifacts/local/my-baseline-v1/protocol.json --runs artifacts/local/my-baseline-v1/runs --output artifacts/local/my-baseline-v1/comparison.json
```

`prepare` selects a published branch/task, checks pinned input manifests and freezes code/input hashes, the three variants, seed 408, controls and budgets. Local freezing does **not** establish independent public preregistration. The launch baseline was frozen after one engineering smoke run of the join variant; the history is disclosed in [development-attempts.md](../../experiments/development-attempts.md). Label exploratory or retrospectively registered work honestly.

`run` starts only the fixed trusted Python engine, with at most three variant executions, 60 seconds each and 180 seconds total by default; it records every attempt before launch. A failure or interruption is retained and stops the loop. Re-running the same directory never silently retries an attempted variant. A stale lock after a process crash requires inspection of retained state before an operator removes that exact lock. An explicitly new protocol/directory is a new locally authorized study, not a way to omit inconvenient earlier work.

`compare` verifies compatible protocol/input/software/output hashes and requires all registered variants, including failed ones. Objective metrics describe manuscript constraints and instrumentation; they never assign contribution points or translation accuracy. The harness bounds inputs, outputs, CPU work and child-process wall time. It executes trusted project code and is **not** a sandbox for submitted programs or a production model runner.

To build an inspectable PR workspace, write an honest AI-use JSON file and supply your actual GitHub identity. `gh api user --jq .id` reports the numeric ID. An example disclosure for executing an unchanged tool without AI assistance is:

```json
{"status":"none","tools":[],"reproducibility_notes":"These unchanged deterministic commands were run without AI assistance; separately disclose any assistance authoring the protocol, code or report."}
```

Save that record at `artifacts/local/my-baseline-v1/ai-usage.json`. Replace the uppercase placeholders below; they are not real identities.

```sh
python tools/research/research.py bundle --id my-baseline-contribution --protocol artifacts/local/my-baseline-v1/protocol.json --runs artifacts/local/my-baseline-v1/runs --comparison artifacts/local/my-baseline-v1/comparison.json --ai-disclosure artifacts/local/my-baseline-v1/ai-usage.json --github-id YOUR_NUMERIC_ID --github-login YOUR_HANDLE
node src/cli.ts validate --manifest contributions/my-baseline-contribution/contribution.json
```

The bundle copies the full protocol, comparison and all attempt records. A routine seed rerun defaults to zero claimed points. Inspect the results; add a distinct family claim only when a useful new finding or capability justifies it. Run the published preflight/optional grader estimate as explained in [CONTRIBUTING.md](../../CONTRIBUTING.md), then review and commit your branch, open a PR, consume the head-bound AI feedback, revise the same branch, and allow the official admission/scoring workflow to respond. Nothing here automatically publishes work.

The actual launch worked example is under [protocols/launch-seed-v1.json](../../protocols/launch-seed-v1.json), [experiments/runs/launch-seed-v1](../../experiments/runs/launch-seed-v1), [experiments/comparisons/launch-seed-v1.json](../../experiments/comparisons/launch-seed-v1.json) and [contributions/launch-seed-worked-example](../../contributions/launch-seed-worked-example). This is real unranked seed work, not fabricated leaderboard activity.

The complete worked bundle is about 218 kB and each full output is about 70 kB. The initial attendant profile allows 40 files, 64,000 bytes per file and 96,000 evidence bytes total: this complete bundle therefore receives an **honest size/inspection hold** under that conservative profile. The demonstration proves local execution and contribution-schema validity; it does not imply production acceptance. [Compact summaries](../../experiments/summaries) are each below 12 kB and retain scalar metrics, length histograms, control/null aggregates, limits and hashes pointing to full outputs. Referencing these outputs does not count as inspecting them. Do not truncate, conceal, split one outcome into extra claims or misrepresent unread evidence to evade a limit. Larger scientific bundles need an explicitly approved bounded inspection/execution capability or a prospective calibrated profile change.

## Data and analytical conventions

The distributed [ZL3b](../../data/manifests/zl3b.json) and [GC2a](../../data/manifests/gc2a.json) files retain exact original bytes and are CC0 according to the host's explicit [transliteration licensing statement](https://voynich.nu/roadmap.html). Their reading lineages differ; GC's v101 is not processed by the EVA numerical normalizer. Original Takahashi HTML pages have different stated download/republication conditions and remain reference-only. No manuscript images, academic PDFs or third-party fonts are silently relicensed.

[Project Gutenberg eBook 11](https://www.gutenberg.org/ebooks/11) is the meaningful English comparison, public domain in the USA. Its complete downloaded text and notices remain in `data/corpora/pg11.txt`; the analysis strips its declared wrapper and extracts lowercase a-z runs. A fixed prefix is used, not a selected best comparison. This is not a historical herbal corpus: that acquisition remains a named gap.

The parser preserves original syntax in the source and supports IVTFF 2.0 page/locus records, foldouts, continuation lines, inline comments and inherited text tags. Tests cover uncertainty, missing headers, duplicates, drawing interruptions, atomic rare codes and known metric invariants. The five baselines use paragraph-type loci; line diagnostics use P0 only and exclude loci with fewer than two retained tokens.

- `join`: choose the first recorded alternate reading, join uncertain spaces, exclude tokens with unreadable/unsupported syntax.
- `split`: choose the first alternate, split uncertain spaces, apply the same exclusions.
- `strict`: exclude tokens containing alternate readings or uncertain spaces, and exclude unreadable/unsupported syntax.

Ligature braces are removed from derived units, case is folded, apostrophes remain encoded units, rare `@nnn;` codes are atomic, and drawing interruptions imply spaces. These are analytical encoding choices, not a recovered glyph alphabet. All exclusion counts are published. Alternative-aware full lattice parsing, image validation and complete ZL/GC alignment remain future work.

Frequency comparisons match token count; entropy without word boundaries matches encoded symbol count and estimates `H(next symbol | previous symbol)` within tokens using observed bigram frequencies. Boundary sensitivity reports a different convention explicitly. Symbol shuffles preserve token lengths and total symbol counts; authored known-plaintext templates and copy/mutate pseudotext are controls, not manuscript evidence or reconstructions of a named historical algorithm.

Clustering uses one fixed k-means initialization on normalized encoded-symbol frequencies. Source metadata uses `I` for illustration category, `H` for the IVTFF Davis-hand convention, `C` for Currier-hand labels, and `Q` for quire. The output compares global and within-quire label shuffles and excludes mixed/unknown H labels from hand NMI. These labels are sourced annotations, not ground truth or proof of meaning.

## Proposed work and evaluator authority

Use [the research proposal interface](../../harness/proposal-interface.json) and the researcher/critic/reproducibility prompts for agent-assisted planning. They never become independent human reviewers. The baseline evaluator, source manifests, control definitions and grading rules live outside a candidate's experimental scratch area. Changing them requires a separately reviewable protocol or software contribution and a new disclosed comparison; it cannot be presented as improving the unchanged evaluator.

Original harness code is Apache-2.0; original documentation/reports are CC BY 4.0. No paid model adapter is required or configured here.
