# Rights record — meaning-probes

- `experiments/meaning-probes/` (protocol, library, five test scripts, verifier scripts,
  results, completeness audit, report) and the run record are original work produced for
  this project; contributed under the repository's licenses.
- `meaning_lib.py` re-implements, with verbatim semantics, the clean parser fixed by the
  adversarial critique (PR #10); it is project-authored code under the repository's
  licenses. The glyph-unit merge list is the frozen output of PR #12's re-segmentation test.
- Voynich corpora: repo-pinned `data/corpora/ZL3b-n.txt` (primary) and
  `data/corpora/GC2a-n.txt` (replication attempt), read-only; see `data/corpora/RIGHTS.md`.
  The zodiac ring and clock positions and the star descriptions are the editorial locus
  codes and comment lines of ZL3b, used as data and cited.
- Positive controls: Culpeper, *The Complete Herbal* (Project Gutenberg 49513, public
  domain in the USA, referenced by sha256, not redistributed); eight written numeral
  series 1–30 (English, Latin, Italian, German, French, Roman, Greek Milesian, d+Roman)
  built into `meaning_lib.py` from common knowledge.
- Direction: Vasily Gnuchev asked, after PR #12, how one would now try to obtain even
  minor meaning; the plan (numerals first, the paragraph-opener formula, the name/grammar
  split) was drafted by Claude Code (`claude-fable-5-1`); the glyph-unit level follows his
  own re-segmentation hypothesis. Tests, adversarial verification and the report were
  produced by a Claude Code multi-agent workflow, model `claude-opus-5`; this manifest, the
  run record and the PR body by Claude Code `claude-fable-5-1`. All disclosed in
  `contribution.yaml`.
- No credentials or private data included.
- Data availability: the corpora used here are served, with the same sha256 hashes, by the Artheon Museum Lab open dataset for MS 408, https://lab.artheonmuseum.org/voynich/ (catalogue: https://lab.artheonmuseum.org/voynich/catalogue.json): transcriptions/ZL3b-n.txt bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc and transcriptions/GC2a-n.txt b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f, byte-identical to the repository's pinned copies. The dataset also carries the 213 page scans that image-based follow-ups (glyph shapes, per-star annotation) will need.
