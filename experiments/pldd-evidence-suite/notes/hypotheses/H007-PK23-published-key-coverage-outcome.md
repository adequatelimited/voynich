# H007-PK23-COV-v1 outcome

Disposition: **rejected**

This outcome record is separate from the frozen protocol so the exact protocol
bytes remain unchanged at SHA-256
`87dd3743413d8eeed08dd7f9eec4bd05dd25413a14fabb3a473d446a56c01501`.

The table-independent guard reproduced the complete frozen exact-consensus
herbal inventory before the published Naibbe table was loaded: 526 logical
lines over 63 physical folios, with 2,341 discovery token occurrences and 777
sealed holdout occurrences. Stage 0 then reproduced all three pinned author
decoder examples byte-for-byte with the published `BASIC=True` and
`MARK_COMPOUND=True` settings.

Discovery results:

| Class | Occurrences | Distinct types |
|---|---:|---:|
| `U` | 797 | 93 |
| `B1` | 937 | 499 |
| `BA` | 82 | 29 |
| `C1` | 27 | 26 |
| `CA` | 3 | 3 |
| `X` | 495 | 374 |

The frozen generator-membership gate failed because `X` was nonzero. The
co-required unique-output gate also failed because both `BA` and `CA` were
nonzero. One occurrence in any of those three classes was sufficient to reject
the direct fixed key; the observed contradictions were therefore decisive.

The complete 777-occurrence holdout remained unevaluated by the published
table. No decoded label, candidate letter pair, decoded word, character stream,
language score, dictionary match, gloss, or translation was released.

This rejects only literal application of Greshko's published fixed reverse
table and published reverse-decoder control flow to the frozen ZL3b/IT2a
consensus corpus and source tokenization. It does not reject a different
historically plausible verbose or homophonic key, a plaintext-letter
permutation, a repaired decoder, different transcription or segmentation, or
the broader Naibbe mechanism.

Validation before the first production run included 21 focused H007 tests, the
100-test repository suite, an independent line-specific code review, and an
author-flow cross-check over 124,669 table-generated synthetic strings with
zero class disagreements. A post-run audit rebuild was byte-identical to all
three production artifacts.

Artifacts:

- `results/h007-pk23-coverage.json`
- `results/h007-pk23-coverage.md`
- `results/h007-pk23-coverage.sha256`
- canonical JSON SHA-256:
  `174e0469312cfbe2d19fe8ad8f435fbd6453a7af9ba1305300140757519b46fd`

Command:

```sh
python3 scripts/analyze_h007_pk23.py
```
