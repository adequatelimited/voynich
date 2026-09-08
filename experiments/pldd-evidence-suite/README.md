# Pinned Voynich evidence suite

This package contributes an IVTFF parser, a Yale canvas index, and the complete
H001–H007 / P001 research sequence. It contains structural observations and
bounded failed or inconclusive hypotheses. It supplies no decipherment,
plaintext, botanical identification, phonetic mapping, or translation.

See [the contribution report](../../contributions/pldd-evidence-suite/REPORT.md)
for the distinct outcomes, relationship to existing voynich.win work, and
limitations; [rights](../../contributions/pldd-evidence-suite/rights.md) covers
the submitted bytes and AI assistance.

## Start here

- [Corpus baseline](results/baseline-zl3b.md): source retention and H001–H003.
- [P001](results/p001-edge-morphology.md): edge-slot morphology control failure.
- [H004](results/h004-local-order.md), [H004-B-v2](results/h004b2-contextual-comparator.md),
  [H004-C](results/h004c-zg-discovery.md): positive static local-order signal,
  invalid contextual comparators, and failed cross-transcription robustness.
  The retracted B-v1 design is preserved in `notes/hypotheses/` as audit history.
- [H005](results/h005-plant-anchors.md): exact-coordinate pharmaceutical-label
  retrieval with 35 source claims, 17 eligible pairs, and failed advancement.
- [H006](results/h006-fr3-line-reset.md): two specified line-reset ternary
  component models rejected at discovery.
- [H007](results/h007-pk23-coverage.md): one published Naibbe key's coverage and
  uniqueness conditions fail on the frozen discovery corpus. The key's author
  did not claim it deciphered the manuscript. The feasibility note records
  why adding arbitrary compounds cannot rescue unique decoding of that test.

## Reproduce

Python 3.11 or newer is required for the standard-library tools. Use Python
3.12 with pandas 2.2.3 for H007, which executes the pinned upstream decoder on
its author's fixtures. The retained H007 run
used Python 3.12.13 and pandas 2.2.3; the publication verification used Python
3.12.14 and pandas 2.2.3 for those controls. The sole report difference is that
recorded Python version. All scientific values are identical.

A local virtual environment is sufficient; no project installation is needed:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install pandas==2.2.3
.venv/bin/python -B -m unittest discover -s tests -v
.venv/bin/python -B scripts/verify_publication.py
```

Run these commands from this directory. If the main interpreter has no pandas,
`H007_PANDAS_PYTHON` can name another interpreter containing pandas. Dependency
selection cannot change corpus, decoder settings, key, or gates.

`verify_publication.py` runs the nine frozen analysis commands sequentially in
temporary output directories, compares outputs with retained artifacts, and
records commands, stdout, elapsed time, and hashes under `verification/rebuilds/`.
The full 9,999-replicate H004 analysis can take several minutes. Unit tests cover
round trips, uncertainty, input hashes, synthetic parser/model fixtures,
strata/inventory guards, negative gate cases, report rendering, and sealed
holdout behavior. Verification is local and AI-assisted; it is not independent
external replication.

The individual analysis entry points remain in `scripts/`; their defaults
rebuild the associated `results/` artifacts. `build_folio_index.py` rebuilds
`data/derived/yale-canvas-index.json` without inferring missing foldout mappings.
There is no H008 entry point or Latin comparator data in this contribution.

## Evidence and selection boundaries

Raw transcriptions, Naibbe inputs, the Yale manifest, and frozen H001–H007/P001
protocols retain their original bytes. Protocol chronology and failed material
variants are in [the scoped research log](notes/research-log.md). The source log
records research dates of July 9–10, 2026; this package was prepared September 8,
2026. Those historical dates are retained records, not an independently
notarized preregistration.

ZL/GC/IT are correlated transcriptions of one manuscript. Source-preserving
parsing does not establish accurate glyph readings, automatic cross-script
conversion, or independent samples. The IIIF index is a convenience and overlaps
with existing Yale-manifest contributions; it is not claimed as new source
acquisition.

H004-C and H005 do not evaluate their reserved IT events. H006 does not compute
its rejected models' held-out residues; H007 does not apply its table to its
777 held-out occurrences. Rebuilding H005 repeats its already-evaluated held-out
retrieval under its original frozen rules. All failed advancement gates remain
in force. The earlier H004-C run's post-breadth-failure permutations are retained
with their disclosed audit chronology, not retroactively represented as a
short-circuited run.

[Publication changes](PUBLICATION-CHANGES.md) itemize packaging edits.
`verification/publication-transforms.json` records the two path-only report
transformations. `SHA256SUMS.txt` inventories submitted files except itself.
