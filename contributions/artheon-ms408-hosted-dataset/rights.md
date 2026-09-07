# Rights record — Artheon MS 408 hosted dataset

Dataset home: https://lab.artheonmuseum.org/voynich/ (Cloudflare R2, anonymous HTTPS read).

## Manuscript scans (213 JPEGs, `scans/`)

- Source: Beinecke Rare Book & Manuscript Library, Yale University, MS 408, via the public
  IIIF service (`https://collections.library.yale.edu/manifests/2002046`).
- Catalog record: https://collections.library.yale.edu/catalog/2002046 — Access: Public.
- The manuscript is a 15th-century work (vellum radiocarbon-dated 1404–1438); the page images
  are faithful reproductions of a public-domain work. Attribution to the Beinecke is retained
  in every catalogue entry (`iiif_image_api` points back to Yale).

## Transliterations (`transcriptions/`)

- RF1b-e, ZL3b-n, GC2a-n, IT2a-n, VT0e-n, FG2a-n, CD2a-n and LSI_ivtff_0d.txt are the
  voynich.nu-hosted transliteration data files (https://www.voynich.nu/data/). The site's
  licensing statement (https://voynich.nu/roadmap.html), inspected by this project on
  2026-09-06, releases its hosted transliteration tables under CC0-1.0. Attribution:
  René Zandbergen (ZL, RF, conversions), Gabriel Landini (ZL), Glen Claston (GC),
  Takeshi Takahashi (IT/TT), the Friedman Study Group (FG), Prescott Currier and
  Mary D'Imperio (CD).
- Cross-check performed 2026-09-06: the hosted `ZL3b-n.txt` is byte-identical to this
  repository's pinned copy (`sha256 bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`,
  411,671 bytes).
- `LSI_text16e6.evt` (original 1998 Stolfi interlinear) comes from Jorge Stolfi's public
  UNICAMP archive; it retains its own terms and is registered **reference_only**.
- `voynich_reference_EVA_clean.txt` is a deterministic derivative of RF1b-e (comments and
  page-property lines removed; locus labels preserved) produced for this dataset; released CC0-1.0.

## Reference documents (`reference/`)

- `manifest.json` — verbatim Beinecke IIIF v3 manifest (public API document).
- `IVTFF_format.pdf` — IVTFF/EVA format specification by René Zandbergen, public at
  https://www.voynich.nu/software/ivtt/IVTFF_format.pdf.

## Dataset index and tooling

`catalogue.json`, `catalogue.md`, `README.md`, `llms.txt`, `download_dataset.py` and the web
page were produced by Artheon Museum Lab for this purpose and are released CC0-1.0.

No credentials, private material or third-party restricted content are included.
