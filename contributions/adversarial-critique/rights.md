# Rights record — adversarial-critique

- `experiments/adversarial-critique/` (protocol, code, report, results, source hashes) and
  the run record are original work produced for this project; contributed under the
  repository's licenses.
- Voynich corpus: repo-pinned `data/corpora/ZL3b-n.txt` (see `data/corpora/RIGHTS.md`),
  read-only, not modified.
- Existing controls reused unchanged: Culpeper (PG 49513), Alice (PG 11), the nine
  bible-corpus translations (Christodoulopoulos & Steedman) referenced by sha256 in
  `experiments/adversarial-critique/results/source_hashes.json`.
- New controls, referenced by sha256 only and **not redistributed**: Chaucer, *Canterbury
  Tales* — Skeat's edition (Project Gutenberg 22120) and Purves' modernised edition (Project
  Gutenberg 2383), public domain in the USA, fetched 2026-09-07 from gutenberg.org.
- The family's parser function is reproduced verbatim from the repository's own pilots for
  the contamination audit; the family's metric formulas are reused unchanged.
- Critique requested by Vasily Gnuchev (2026-09-07). AI agent: Claude Code, model
  `claude-fable-5-1` (Anthropic) — protocol design, implementation, drafting; disclosed in
  `contribution.yaml`.
- No credentials or private data included.
- Data availability: the corpora used here are served, with the same sha256 hashes, by the Artheon Museum Lab open dataset for MS 408, https://lab.artheonmuseum.org/voynich/ (catalogue: https://lab.artheonmuseum.org/voynich/catalogue.json): transcriptions/ZL3b-n.txt bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc and transcriptions/GC2a-n.txt b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f, byte-identical to the repository's pinned copies. The dataset also carries the 213 page scans that image-based follow-ups (glyph shapes, per-star annotation) will need.
