# Transliteration and corpus policy

Transliteration encodes visible shapes. A code point need not equal a manuscript glyph, grapheme, letter or sound; an apparent space need not divide words. Preserve raw source bytes, headers, uncertainty, alternative readings, locus identities and version history before deriving normalized data.

ZL3b and GC2a are independently produced readings with different alphabets, later converted into common IVTFF metadata conventions. Converted copies of a single reading are not independent evidence. Shared page/hand labels do not make independent readings independently labeled corpora.

Each analysis records included locus types, drawing breaks, alternatives, unreadable regions, rare signs, ligatures, case and spacing choices, along with all exclusions. Unknown or unsupported input fails or is explicitly excluded with counts. A parser cannot quietly turn commentary into manuscript text, plant hypotheses into factual labels, or one alphabet into another without a documented mapping.

The source-specific [folio index](../data/derived/folio-index.json) preserves numbered panels and `fRos`. Physical leaves, sides, foldout panels, transcription units and scans remain separate counts. Official image references are custodian links; unknown canvas identifiers remain null.

The initial parser supports the documented IVTFF subset and has actual-corpus and synthetic-format tests. Full glyph-accuracy evaluation, alignment to GC, uncertain-reading lattices and image/locus mapping remain open tasks. See [the harness conventions](../tools/research/README.md) and the [IVTFF specification](https://voynich.nu/software/ivtt/IVTFF_format.pdf).
