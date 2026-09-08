# Rights record — clean-rerun

- `experiments/clean-rerun/` (protocol, code, report, results) and the run record are
  original work produced for this project; contributed under the repository's licenses.
- `family_generators.py` reproduces, unchanged and with per-function provenance, generator
  code from this repository's own pilots (PRs #3–#6); `critique_lib.py` is a verbatim copy
  of `experiments/adversarial-critique/adversarial_critique.py` from PR #10. Both are
  project-authored code under the repository's licenses.
- Voynich corpus: repo-pinned `data/corpora/ZL3b-n.txt` (see `data/corpora/RIGHTS.md`),
  read-only, not modified. Controls reused unchanged: Culpeper (PG 49513) and the Latin
  Vulgate from the bible-corpus (Christodoulopoulos & Steedman), referenced by sha256.
- Re-run requested by Vasily Gnuchev (2026-09-07). AI agent: Claude Code, model
  `claude-fable-5-1` (Anthropic); disclosed in `contribution.yaml`.
- No credentials or private data included.
- Data availability: the corpora used here are served, with the same sha256 hashes, by the Artheon Museum Lab open dataset for MS 408, https://lab.artheonmuseum.org/voynich/ (catalogue: https://lab.artheonmuseum.org/voynich/catalogue.json): transcriptions/ZL3b-n.txt bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc and transcriptions/GC2a-n.txt b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f, byte-identical to the repository's pinned copies. The dataset also carries the 213 page scans that image-based follow-ups (glyph shapes, per-star annotation) will need.
