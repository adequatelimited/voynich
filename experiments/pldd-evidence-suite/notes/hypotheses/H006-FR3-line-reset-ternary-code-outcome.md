# H006-FR3-LINE-v1 outcome

Disposition: **rejected**

This outcome record is separate from the frozen protocol so the exact protocol
bytes remain unchanged at SHA-256
`88e75dd64fa0af6554a613b7d0d1120619f63d18785133febfeb0bfabb0ed96f`.

The guarded inventory reproduced all frozen feasibility counts before any
component expansion: 1,185 eligible exact ZL/IT consensus lines over 92
physical folios, split into 919 discovery lines over 69 folios and 266 sealed
holdout lines over 23 folios. Every discovery breadth gate passed.

Discovery results:

| Model | Residue 0 | Residue 1 | Residue 2 | Contradictions | Exact gate |
|---|---:|---:|---:|---:|:---:|
| `PAIR` | 321 | 297 | 301 | 598 | fail |
| `OPTIONAL_E` | 326 | 303 | 290 | 593 | fail |

Both project-instantiated component models therefore contradict the necessary
all-lines divisibility condition on most clean discovery lines. Neither model
qualified. The held-out primitive counts and residues were not computed or
reported, no component model was locked, and no key/plaintext stage was
authorized.

This rejects only the conjunction tested by H006-FR3-LINE-v1: the frozen
Matlach-inspired component tables, fixed three-trit blocks, and independent
phase-zero reset on every IVTFF logical prose line. It does not reject a
continuous or paragraph-reset frame, another component table, a variable-length
code, historical homophony generally, or a Naibbe-like verbose cipher.

No decoded string, language score, dictionary lookup, word segmentation,
phonetic value, semantic gloss, or translation was produced.

Artifacts:

- `results/h006-fr3-line-reset.json`
- `results/h006-fr3-line-reset.md`
- `results/h006-fr3-line-reset.sha256`
- canonical JSON SHA-256:
  `192845597048b3655debadd50661bebdf08b741bb28ecb23146811a59fc963c7`

Command:

```sh
python3 scripts/analyze_h006_fr3.py
```

