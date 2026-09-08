# Large-artifact inspection release

Operator-authorized on 2026-09-07: add large-artifact handling and exclude all video and archive/compressed content. Profile v4 preserves Sonnet, existing qualitative tiers, inclusion-first admission, signed credit and all existing awards. No calibration success is claimed.

## Large artifacts: current v4 release (2026-09-07)

The active profile admits up to **160 files, 4,000,000 source bytes per file and 24,000,000 source bytes per submission**, including referenced evidence. These are decimal bytes. AI evidence content remains at most **96,000 bytes**; the existing 256,000-byte complete stage envelope and four-call maximum remain unchanged. No new upload route, Git LFS dependency or archive extraction is introduced: originals stay in the PR and are retrieved by immutable Git blob identity.

The public `src/artifacts.ts` implementation uses `file-type` for binary signature identification and `csv-parse` for CSV/TSV inspection. A positive text-format allowlist, binary checks, fatal UTF-8 decoding, full-source known-secret scan, bounded structural validation and full-source SHA-256 run before representation. JSON/JSONL must parse; CSV records are limited to 64,000 characters of parser record buffer and 4,096 columns. No submitted code executes. Content-signature detection and secret patterns are checks, not a malware certificate.

Manifests, rights, reports, notebooks and executable source must fit fully in the evidence allocation. Larger TXT, CSV, TSV, JSON and JSONL datasets may receive a deterministic representation with structural counts and five byte-positioned excerpts. Allocation sorts paths, reserves full small/critical files and 2,000 bytes per large data view, then distributes the remaining evidence space. A raw source hash/size and a separate representation hash/size/method/budget bind the view. Official merge settlement recomputes derived views from the merged original bytes. Local previews use the same inspector and allocation; include the same changed and referenced files for parity.

This is **full-byte structural inspection with partial semantic coverage**, not full AI reading, antivirus certification, independent reproduction or proof of data accuracy. Useful, attributable data may be admitted and scored on supported utility; unseen detail cannot support stronger claims or higher tiers. Manifests must state purpose, source, rights and how the artifact supports the outcome. Large files do not earn volume bonuses. Concrete prohibited content still blocks. If essential evidence exceeds the published envelope, submit a focused report and independently useful scope; do not fragment one outcome to multiply credit.

Video and all archives/compressed containers are prohibited, including archive-based Office documents, EPUB/NPZ, and renamed payloads. Nothing is unpacked. GIF and animation-capable submitted animation formats are excluded conservatively. Active/binary outputs embedded in notebooks are unsupported. PDF and still-image uploads retain their existing requirement for an authorized isolated/visual inspection adapter; this text-data release does not pretend OCR or metadata alone satisfies it. A bibliographic reference to an external work is still evaluated as submitted metadata, not automatically downloaded.

See [release record](grading/releases/2026-09-07-large-artifacts.md) and the [active profile](grading/profiles/active.json). This section supersedes older text-only size and mandatory-full-model-reading language for the supported bounded-text-v1 data representation.

