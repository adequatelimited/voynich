# H004-C pre-IT ZL/GC discovery

> STA-family structural analysis only. This analysis did not load IT bytes or project IT event data; the pinned IT file had prior integrity/header inspection before protocol freeze.

- Protocol: `H004-C-v1`
- Protocol SHA-256: `be0abd73d82c8c4660483191a6083e5b0167934736060fc2832c2af5b6916c18`
- Manifest SHA-256: `fddeea50665674bef82b88ed47f2040a51a2e0b9e4662c72e33e0548d4785c32`
- Joint permutations run / requested: 9999 / 9999
- Reserved pages with targets / targets: 38 / 648
- Valid / invalid aligned positions: 3737 / 405
- Movable targets: 614 (94.75%)
- Currier A pages / targets: 21 / 174
- Currier B pages / targets: 17 / 474
- Pre-IT ZL/GC gate: `not met`

## Execution chronology

The strict ZL/GC skeleton failed the frozen breadth gate. The implementation nevertheless completed and exposed the ZL/GC permutation results before a short-circuit correction was requested. Those already-inspected results are retained as audit evidence; they also fail the effect gates and cannot authorize IT event projection.

| Witness | Metric | Observed | Null mean | Delta | Monte Carlo p | Positive pages |
|---|---|---:|---:|---:|---:|---:|
| ZL | C: exact or one edit | 0.560249 | 0.545394 | +0.014855 | 0.297300 | 22 |
| ZL | U: one edit, no exact | 0.397834 | 0.411357 | -0.013523 | 0.670500 | 19 |
| ZL | E: exact repeat (diagnostic) | 0.162415 | 0.134038 | +0.028378 | 0.077200 | 20 |
| GC | C: exact or one edit | 0.561819 | 0.545909 | +0.015910 | 0.285400 | 23 |
| GC | U: one edit, no exact | 0.399403 | 0.411842 | -0.012439 | 0.657300 | 20 |
| GC | E: exact repeat (diagnostic) | 0.162415 | 0.134067 | +0.028349 | 0.076600 | 20 |

## Currier checks

| Witness | Currier | Metric | Targets | Delta | Monte Carlo p | Gate |
|---|---|---|---:|---:|---:|:---:|
| ZL | A | C | 174 | +0.017662 | 0.309200 | no |
| ZL | A | U | 174 | +0.022336 | 0.269200 | no |
| ZL | B | C | 474 | +0.076153 | 0.000100 | yes |
| ZL | B | U | 474 | +0.043959 | 0.021200 | yes |
| GC | A | C | 174 | +0.021836 | 0.255700 | no |
| GC | A | U | 174 | +0.027709 | 0.215100 | no |
| GC | B | C | 474 | +0.070226 | 0.000600 | yes |
| GC | B | U | 474 | +0.037763 | 0.042000 | no |

Disposition: reject H004 as a ZL/GC-robust STA-family route; leave IT event projection unrun.

The JSON manifest records every aligned position, frozen target/context ID, exclusion, reset, cell, input/specification hash, and page residual. Witness tuples were shuffled jointly; witness p-values were not pooled.
