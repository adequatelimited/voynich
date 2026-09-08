# H006-FR3-LINE fixed-three-trit frame screen

Machine-readable JSON SHA-256: `192845597048b3655debadd50661bebdf08b741bb28ecb23146811a59fc963c7`

Disposition: **reject H006-FR3-LINE-v1: neither frozen component model met the exact discovery line-frame condition; held-out residues remain sealed**

## Boundary

This deterministic screen tests line-length divisibility only. It emits no
plaintext, language, word segmentation, dictionary result, or gloss. No iid
null or p-value is part of the frozen protocol.

## Exact-consensus inventory

- Aligned locus keys audited: 5386
- Eligible lines: 1185
- Excluded keys: 4201
- Discovery lines / folios: 919 / 69
- Sealed-holdout lines / folios: 266 / 23

## Eligibility attrition

Exclusion counts are multi-label: one key can contribute to every
applicable reason below, but no key enters the eligible inventory twice.

- Keys with ZL brace notation: 406
- Keys with IT brace notation: 0
- Admitted keys with brace notation in either witness: 42
- Excluded keys with brace notation in either witness: 364

| Exclusion reason | Keys |
| --- | ---: |
| `invalid_locator` | 1 |
| `invalid_physical_folio` | 160 |
| `it_excluded:unreadable_glyph` | 115 |
| `it_no_certain_token` | 22 |
| `midword_n` | 104 |
| `missing_or_duplicate_it_locus` | 171 |
| `missing_or_duplicate_zl_locus` | 1 |
| `nonprose_locus` | 1256 |
| `outside_frozen_sign_inventory` | 141 |
| `zl_excluded:alternative_reading` | 728 |
| `zl_excluded:apostrophe` | 101 |
| `zl_excluded:extended_eva` | 132 |
| `zl_excluded:joined_eva_form` | 1 |
| `zl_excluded:uncertain_word_space` | 1833 |
| `zl_excluded:unreadable_glyph` | 225 |
| `zl_excluded:unsupported_symbol` | 132 |
| `zl_it_token_disagreement` | 3314 |
| `zl_metadata_outside_frozen_domains` | 755 |
| `zl_no_certain_token` | 140 |

## Discovery

- Breadth gate: pass
- Qualifying models: none
- Locked model: none

| Model | Residue 0 | Residue 1 | Residue 2 | Contradictions | Exact gate |
| --- | ---: | ---: | ---: | ---: | :---: |
| `PAIR` | 321 | 297 | 301 | 598 | fail |
| `OPTIONAL_E` | 326 | 303 | 290 | 593 | fail |

## Held-out stage

Held-out residues were not computed or reported and remain sealed.

- Holdout breadth gate: pass
- Key/plaintext stage authorized: false

## Input hashes

- `it_eva`: `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5`
- `protocol`: `88e75dd64fa0af6554a613b7d0d1120619f63d18785133febfeb0bfabb0ed96f`
- `zl_eva`: `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`
