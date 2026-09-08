# P001: atomic edge-slot morphology discriminating-control pilot

Status: **failed discriminating control; no morphology or gloss advanced**

## Validity disclosure

P001 records a simultaneous scratch protocol and evaluation. The rules,
thresholds, and partition outputs were inspected in the same research session.
It is neither preregistered nor confirmatory, and the `calibration` and `test`
partition names do not imply untouched evidence. The exact scratch split tag,
`H004-v1`, is retained rather than relabeled after inspection. This pilot is
named P001 so H004 remains available for the separately frozen local
predictive-order hypothesis.

The scratch exploration considered longer edge strings before the recorded
calculation restricted the proposed slots to one STA family. That restriction
is a disclosed analytical degree of freedom and another reason not to treat
the result as confirmation.

## Claim tested

If a small inventory of atomic edge families behaves as detachable morphology,
a training-selected optional prefix and suffix inventory should generate unseen
prefix/core/suffix combinations at a rate that is distinctive relative to
arbitrary equal-cardinality edge inventories.

This claim concerns a possible transcription-level production mechanism. It
does not assign language, sound, meaning, grammatical category, or a gloss.

## Reproducible protocol

- Input: pinned `data/raw/transcriptions/sta1/ZL3b.txt`.
- Include substantive `P*` loci only.
- Word unit: a component bounded by certain spaces or drawing boundaries.
  Reject uncertain spaces, alternative readings, `?`, unreadable `Z1`, and
  malformed components.
- Analytical unit: one two-character STA1 code, which may represent a composite
  rather than a manuscript glyph. Reduce it to its first-character family for
  this pilot.
- Page split: first byte of `SHA256("H004-v1:" + page_id)`; `<154` is train,
  `154–204` calibration, and `>=205` test.
- Candidate slot: one family at the word's left or right edge.
- Select from train only when the family has at least 10 distinct edge
  residuals, 50 edge tokens, and 80% edge exclusivity among train types that
  contain it anywhere.
- The rule selects prefix `D` and suffixes `G` and `H`.
- Segment deterministically as optional `D | nonempty core | optional G/H`.
  Prefix stripping has priority when a two-family word could otherwise lose
  its entire core.
- A productive evaluation type is absent as a surface type from train, has a
  selected edge family, has a core found in the train core inventory, and has
  a complete slot tuple absent from train.
- Discriminating control: exhaustively evaluate every inventory containing one
  prefix family and an unordered pair of suffix families from the 22-family
  train alphabet. The 5,082 inventories include the selected one.
- Advancement criterion: selected-inventory test rate at or above the 95th
  percentile of those equal-cardinality inventories.

## Result

- Train: 130 pages, 19,031 tokens, 2,822 family types.
- Calibration: 33 pages, 4,150 tokens, 1,085 types; 45 of 76 unseen affixed
  types were productive (59.21%).
- Test: 44 pages, 6,610 tokens, 1,505 types; 69 of 123 unseen affixed types were
  productive (56.10%). The 69 types were 11.58% of all 596 unseen test types.
- Of the 5,082 equal-cardinality inventories, 2,308 had a strictly higher test
  productive rate. The selected inventory ranked 2,309th, at the 54.58th
  percentile.

The 95th-percentile advancement gate failed decisively. The observed
recombination is real as a descriptive property, but it is not distinctive:
many arbitrary inventories perform as well or better.

Disposition: **do not advance `D`, `G`, or `H` as morphological slots; assign no
gloss; retain P001 as a negative control for future segmentation proposals.**

Generated evidence:
`results/p001-edge-morphology.json` and
`results/p001-edge-morphology.md`.

Command:

```sh
python3 scripts/analyze_edge_morphology.py
```
