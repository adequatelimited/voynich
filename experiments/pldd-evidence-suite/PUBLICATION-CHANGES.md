# Publication changes and preserved evidence

The package mirrors the original research layout; source workspace files were
not modified. The following publication edits are explicit and do not revise
scientific rules or outcomes.

1. Exclude the future H008 design, all Latin comparator inputs, compiled Python
   caches, repository instructions, and unrelated files. Scope the research log
   and data provenance to the included work. Remove the one Latin-specific
   provenance test and four excluded Latin raw-file hash entries. The other
   original tests remain, with the portability changes below.
2. Rename four checksum sidecars from `.sha256` to `.sha256.txt` for the public
   artifact inspector. Update their script/test references; checksum contents
   are unchanged except for the two intentionally transformed JSONs below.
3. Relocate the byte-identical Yale manifest from `data/raw/manifests/` to
   `data/raw/iiif/`, updating its builder, fixture/hash tests, and provenance.
   This lets the inspector classify a 403,042-byte external data object as data.
   It does not alter the canvas index, manifest content, URL, or pinned hash.
4. Remove H007's workstation-specific fallback interpreter. The existing
   current interpreter, `H007_PANDAS_PYTHON`, and explicit interpreter candidates
   remain. No decoder settings or data inputs change.
5. Replace eight absolute input-path metadata values in the H004-C and H005
   JSONs with package-relative paths. Rerender their Markdown and checksum
   sidecars with the new artifact hashes. Their frozen protocols, source
   ledger, parameters, statistics, and gate decisions are unchanged. The
   JSON-pointer audit and original/published hashes are retained in
   `verification/publication-transforms.json`. Apply the same relative path
   serialization in the two analysis entry points for reproducible rebuilds.
6. The original H007 freshness test expected a report hash that embeds Python
   3.12.13. The available pandas interpreter is now Python 3.12.14. The first
   publication test run is retained as a failure. The package test verifies
   the unchanged historical JSON's exact original hash, compares the new JSON
   byte-for-byte after replacing only the recorded Stage-0 runtime metadata
   with the historical metadata, and still enforces all original discovery,
   seal, renderer, and sidecar checks. Actual runtime versions and the sole
   observed JSON delta are separately recorded. No claim of byte identity
   between those differently labelled runtime reports is made.
7. Correct the Naibbe provenance wording: the vendored `LICENSE` is standard
   MIT text; its pinned `README.md` adds citation-condition language. Retain
   both unchanged, cite the publication, and defer to the contribution rights
   record for the documented interpretation.
8. Add this change log, a package README, a deterministic rebuild driver,
   publication verification records, and a SHA-256 inventory. New publication
   tooling does not evaluate any newly reserved test material.

All H001–H007 and P001 protocol files, including retracted H004-B-v1 and its
replacement, remain byte-identical. The original H006 and H007 canonical JSONs
retain SHA-256 `192845597048b3655debadd50661bebdf08b741bb28ecb23146811a59fc963c7`
and `174e0469312cfbe2d19fe8ad8f435fbd6453a7af9ba1305300140757519b46fd`.
