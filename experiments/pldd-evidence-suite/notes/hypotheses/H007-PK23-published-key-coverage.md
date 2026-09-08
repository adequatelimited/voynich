# H007-PK23-COV: published Naibbe-key coverage screen

Status: **frozen before any Voynich table-membership or decoder-output
outcome under this exact protocol**

Protocol version: `H007-PK23-COV-v1`

## Claim boundary

H007-PK23-COV-v1 is the cheapest exact falsifier of one narrow route: apply
Michael A. Greshko's published Naibbe reverse table and published reverse
decoder literally, with the author's plaintext-letter labels unchanged, to
strict ZL3b/IT2a consensus prose on herbal pages.

There is no key search, no 23-letter permutation, no table completion, no
glyph substitution, and no choice between decoder variants. The fixed settings
are `BASIC=True` and `MARK_COMPOUND=True`. Exact unigram readings therefore
take priority over every possible prefix/suffix reading, and compound recovery
is attempted only where the published decoder attempts it.

A failure rejects this **direct published fixed-key decoder** on this frozen
corpus and segmentation. It does not reject the broader Naibbe mechanism, a
different historically plausible verbose/homophonic key, a plaintext-letter
permutation, a different transcription, or a repaired decoder. A complete
pass establishes only deterministic fixed-table coverage and uniqueness. It
does not establish a language, word segmentation, grammar, semantic reading,
historical use of the key, or translation.

This is a coverage stage only. It may report the six token classes `U`, `B1`,
`BA`, `C1`, `CA`, and `X`, plus aggregate gates and provenance. It may not emit
or persist a decoded letter, candidate letter pair, decoded word, character
stream, plaintext line, language score, dictionary match, gloss, or fluent
rendering. Even a complete holdout pass authorizes only a separately frozen
plaintext/output protocol.

## Published source and immutable pins

- Primary publication: Michael A. Greshko, “The Naibbe cipher: a substitution
  cipher that encrypts Latin and Italian as Voynich Manuscript-like
  ciphertext,” *Cryptologia* (2025),
  <https://doi.org/10.1080/01611194.2025.2566408>.
- Author repository: <https://github.com/greshko/naibbe-cipher>, pinned at
  commit `f2675ec5dd275268bc64dd48ea64fc0e0e9827a2`.
- Published reverse table, `references/naibbe_tables.csv`, SHA-256
  `4e7cfd54b7ec66515d39a51e11ec97e8e19b643b0b189124eebc3982e707dcec`.
- Published reverse decoder, `decrypt_naibbe.py`, SHA-256
  `1c18514bbaba914989f1961f41a3930b7c1afe81d6db37b07b1dd7d9e6ea3b49`.
- Published encoder used only to delimit the mechanism claim, `naibbe.py`,
  SHA-256
  `3f5e353d2c50f4e6a6b81567ca31cee4f0537a490b6346d054d26661648a6003`.

The selected upstream files, author examples, README, and modified-MIT license
are mirrored byte-for-byte under
`data/raw/external/naibbe-f2675ec/`. Their individual hashes and source paths
are recorded in `data/PROVENANCE.md`; the local mirror prevents a network or
moving-branch lookup from entering the run.

The pinned CSV contains 414 role entries: 138 unigram, 138 prefix, and
138 suffix entries across six tables, using 23 published plaintext-letter
labels and 356 distinct ciphertext strings. These are integrity facts, not
Voynich coverage results.

The paper's 52-card and 78-card constructions change forward selection
weights. They do not change this CSV or the published inverse function, which
does not accept a deck-size argument. H007-PK23-COV-v1 therefore has no 52/78
branch and makes no claim about the forward probability of an observed trace.

Pinned manuscript and parser inputs:

- ZL3b-n, extended EVA/IVTFF source of record, SHA-256
  `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`.
- IT2a-n, historical Takahashi-derived EVA comparison, SHA-256
  `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5`.
- The exact pre-freeze `src/voynich/ivtff.py` parser, SHA-256
  `54d915b772d929f3ac5446ec19cbd1c5799956f43cdf5a6bfbb81279da7f693b`.

Before corpus inventory, verify both transcription hashes, require IVTFF
alphabets `Eva-` for ZL and `EvaT` for IT, parse both with the pinned parser,
and require each parsed document to emit its input bytes unchanged. Any hash,
header, parse, or round-trip failure aborts before the Naibbe table is loaded.
ZL and IT are correlated transcriptions of one manuscript, not independent
samples.

## Frozen exact-consensus corpus

The observation called a line is one parsed IVTFF logical locus keyed by
`(page_id, locus_number)`. Source continuations remain one locus. A locus is
eligible only if all of these conditions hold:

1. Exactly one ZL locus and one IT locus exist at the key.
2. The page identifier matches `^(f\d+)[rv]\d*$`; its first capture is the
   physical folio. `fRos` and any other nonmatching identifier are excluded,
   not assigned by hand.
3. Both witnesses mark the locus as prose (`P*`), and neither locator is `!`.
4. The effective ZL illustration variable is exactly `$I=H`.
5. `tokenize_certain_basic_eva` produces at least one token in each witness
   and excludes no component in either witness. Thus certain dots and drawing
   breaks delimit tokens; inert comments are removed; ligature braces are
   flattened while preserving their contents; and an uncertain space,
   alternative, unreadable glyph, Extended-EVA code, joined uppercase form,
   malformed ligature, or unsupported symbol invalidates the complete line.
6. The complete ordered Basic-EVA token tuple is identical in ZL and IT after
   that documented tokenization. No disagreement is deleted, repaired,
   respaced, or reduced to a partial consensus.

There is no extra sign-inventory restriction and no manual token deletion.
The shared tokenizer regards an apostrophe as a token character, so this
protocol does not silently add an apostrophe exclusion; the frozen eligible
inventory happens to contain zero apostrophe-bearing tokens, a
table-independent fact.
The source token boundaries are treated as candidate ciphertext boundaries
for this narrow route, not as established plaintext word spaces. The one
eligible line lacking ZL Currier `$L` remains in scope as `unknown`; it may not
be dropped after an outcome.

Derive the physical-folio split with the exact ASCII rule

`first_byte(SHA256("H007-PK23-COV-v1:" + physical_folio)) < 51`.

All sides and panels of a physical folio remain together. The inventories
below were computed using only the pinned parser, corpus metadata, token
equality, and the split hash. Neither the Naibbe CSV nor decoder was loaded by
that computation.

| Scope | Logical lines | Page/panel IDs | Physical folios | Token occurrences | Distinct token types |
|---|---:|---:|---:|---:|---:|
| Overall | 526 | 124 | 63 | 3,118 | 1,261 |
| Discovery | 385 | 91 | 46 | 2,341 | 1,024 |
| Sealed holdout | 141 | 33 | 17 | 777 | 451 |

Frozen breadth by ZL metadata:

| Scope | Currier lines A/B/unknown | Currier tokens A/B/unknown | Hand lines 1/2/3/5 | Hand tokens 1/2/3/5 |
|---|---:|---:|---:|---:|
| Overall | 445/80/1 | 2,508/602/8 | 445/57/18/6 | 2,508/418/141/51 |
| Discovery | 329/55/1 | 1,914/419/8 | 329/48/5/3 | 1,914/358/36/33 |
| Sealed holdout | 116/25/0 | 594/183/0 | 116/9/13/3 | 594/60/105/18 |

The 17 held-out physical folios are `f4`, `f6`, `f7`, `f16`, `f19`, `f22`,
`f25`, `f31`, `f33`, `f35`, `f36`, `f41`, `f42`, `f53`, `f54`, `f66`, and
`f95`. Discovery and holdout share 214 token types; 810 types occur only in
discovery and 237 only in holdout. The split is therefore whole-folio but not
type-disjoint. Since the key is fixed before either partition there is no
type fitting, but repeated discovery types partly reveal deterministic
holdout compatibility. The holdout is a whole-folio replication gate, not an
independent key-learning experiment.

An implementation must reproduce every count, stratum, folio assignment, and
type-overlap count above exactly before loading the Naibbe table. A mismatch is
an invalid run and is `inconclusive`; it does not authorize a near-match
inventory or membership computation.

## Stage 0: literal author-decoder validation

Stage 0 may decode only the author's pinned example ciphertexts. It must not
load, pass, hash against the table, or otherwise inspect any manuscript token.

Use the byte-identical local mirror of the unmodified files at the pinned
commit. Verify the table, decoder, encoder, control-input, and control-output
hashes above. Import the pinned `decrypt_naibbe.py` with its global
`BASIC=True` and `MARK_COMPOUND=True`, and call its published
`decrypt_naibbe_file` with `basic=True`, the pinned CSV, and a temporary output
path for each pair below. Compare the generated UTF-8 output bytes exactly
with the pinned author output; do not normalize whitespace, stars,
parentheses, line endings, or final newlines.

| Author ciphertext | Ciphertext SHA-256 | Author decoded output | Output SHA-256 |
|---|---|---|---|
| `encrypted/examples/endofpaper.txt` | `475055654de0049675c26de7550a37426045e4a57ab533cb97677b390e4764d7` | `decrypted/examples/endofpaper_decrypted.txt` | `c89ca7e66548d76728d968a741296405a271000534f6946d76737fafe7a288c6` |
| `encrypted/examples/gallic_naibbe.txt` | `c813aa51a843a7c399c4707b000155ba615b00ffe34276054a6e2838cfcc8ae2` | `decrypted/examples/gallic_decrypted.txt` | `c439209d7a3f5492e0adb68505316392ea8b5c25ec7b53605c2d43d27d85ce68` |
| `encrypted/nathist_output_ciphertext.txt` | `9cdf2de12f371ac7efdb2e78713f229ada508286c1717758184238a59cd64326` | `decrypted/nathist_output_ciphertext_decrypted.txt` | `852d1ad67f82d6472c8ef1d99bfa12c62f76f3d37be2623a131f47232b753ca2` |

All three comparisons must pass. Record the Python and pandas versions as
environment metadata, but they are not free parameters. A missing dependency,
hash mismatch, exception, or byte mismatch makes the run `inconclusive` and
aborts before any manuscript table membership is evaluated. Do not patch the
decoder or replace a golden artifact after a failure.

## Exact class observer

After Stage 0 passes, the manuscript runner may use the pinned reverse maps
and the exact published control flow only as a class observer. Plaintext
letter labels are opaque internal identifiers used where the author decoder
deduplicates candidates; they are never serialized, logged, joined into a
line, returned in a report, or shown to a researcher.

Class each complete source token as follows, in this priority order:

- `U` — the exact token is present in the published unigram map. Under
  `BASIC=True`, this wins even if prefix/suffix parses also exist.
- `B1` — there is no `U`, and enumeration of every nonempty prefix/suffix
  split produces exactly one distinct decoded two-letter result after the
  decoder's order-preserving deduplication.
- `BA` — there is no `U`, and that same enumeration produces more than one
  distinct decoded two-letter result.
- `C1` — there is no direct unigram or bigram result; the published compound
  routine finds exactly one viable split into exactly two ciphertext pieces;
  both pieces are in `all_word_types`; recursive compounding is disabled; and
  each child decoding is itself unique.
- `CA` — the compound routine finds at least one viable split, but it finds
  multiple viable splits or at least one viable split contains an ambiguous
  child decoding. Compound candidates are not newly deduplicated. The
  published closest-to-even-split star is only a display heuristic and never
  converts `CA` to `C1`.
- `X` — none of the preceding published-decoder paths succeeds.

`U`, `B1`, and `BA` are direct published-token constructions. `C1` and `CA`
are constructions recognized by the published decoder's exact two-piece
compound fallback. All five are counted as generator membership for this
screen; `X` is not. Only `U`, `B1`, and `C1` have unique published-decoder
output.

This definition deliberately inherits the published implementation's limits.
In particular, the encoder's repeated probabilistic space removal can in
principle concatenate three or more adjacent generated tokens, while the
published reverse decoder recursively resolves no more than two. An `X` that
would require a longer compound still rejects the **direct published reverse
decoder** here; it does not reject a separately frozen repaired decoder or the
general forward generator.

## Stage 1: discovery coverage

Only after all input checks and Stage 0 pass, classify all 2,341 discovery
token occurrences in deterministic `(page_id, locus_number, token_index)`
order. Complete the full discovery inventory even after a contradiction, but
never evaluate a holdout token in the same run unless every discovery gate
passes.

The discovery artifact may contain only:

- the pinned artifact hashes and reproduced table-independent inventories;
- Stage 0 pass/fail;
- one aggregate six-row `U/B1/BA/C1/CA/X` histogram, with occurrence and
  distinct-type counts;
- the two exact gate booleans and disposition.

It must not contain token strings, token hashes, folio or locus outcomes,
candidate counts below the six classes, exceptions, closest alternatives, or
any plaintext label. This prevents a failed token from becoming a prompt for
post-hoc repair.

The two co-required deterministic gates are:

1. **100% generator membership:** `X = 0`, equivalently
   `(U + B1 + BA + C1 + CA) / 2,341 = 1.000000`.
2. **100% unique published-decoder output:** `BA = 0` and `CA = 0`,
   equivalently `(U + B1 + C1) / 2,341 = 1.000000` once membership passes.

One `X`, `BA`, or `CA` occurrence rejects H007-PK23-COV-v1 as a direct fixed
key. There is no error budget, manual exception, majority reading, star-based
choice, token deletion, respacing, table relabeling, or best-coverage
fallback. On discovery rejection, the holdout remains unevaluated by the
table and every plaintext output remains sealed.

This is an exhaustive necessary-condition test, so no stochastic null,
p-value, language model, or dictionary baseline is computed.

## Sealed holdout

Only a complete discovery pass authorizes the exact same class observer on
all 777 held-out token occurrences. Re-verify the frozen holdout inventory and
do not change any setting, parser rule, map, priority, class rule, or report
schema.

Report only the aggregate six-class occurrence/type histogram and gates. The
holdout requires `X = BA = CA = 0`, which is the same 100% membership and 100%
unique-output condition as discovery. Process the complete holdout after it is
authorized; do not stop at the first contradiction.

One held-out `X`, `BA`, or `CA` rejects the direct fixed key. A complete pass
marks only `published fixed-table coverage and uniqueness` as `promising` and
authorizes a new, separately frozen H007 plaintext/output protocol. This
coverage stage never releases the internally referenced letter labels or
reruns an output-producing decoder on manuscript text.

## Contamination and leakage disclosure

The Naibbe table was designed to generate Voynich-like ciphertext using
Voynich-derived forms and distributional targets. Its manuscript token
membership is therefore not an independent prediction. High `U/B1/C1`
coverage, even on a whole-folio holdout, may be a design consequence and is
not evidence by itself that the manuscript used this key. The author examples
in Stage 0 validate software identity and behavior, not the manuscript claim.

Before this file was frozen, the published table geometry and decoder source
were audited to define a minimally free test, and the table-independent corpus
inventory above was computed. No exact ZL3b/IT2a token was compared with the
Naibbe table, no manuscript class histogram or coverage value was inspected,
and no manuscript plaintext letter or string was decoded. These rules and
counts may not be retuned after the first membership outcome.
