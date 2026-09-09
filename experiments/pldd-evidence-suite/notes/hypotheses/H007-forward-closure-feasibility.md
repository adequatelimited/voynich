# Post-H007 forward-closure feasibility audit

Disposition: **no-run; cannot authorize a unique reading**

This is a logical and table-only follow-up to H007-PK23-COV-v1. It does not
alter the frozen H007 protocol, inspect any token-level manuscript outcome, or
evaluate the sealed holdout.

## Proposed repair

The published encoder first emits one ciphertext atom for a plaintext unigram
or bigram and then independently removes ciphertext spaces with nonzero
probability. Consecutive removals can therefore concatenate more than the two
atoms handled by the published reverse decoder. The natural parameter-free
repair would:

1. read the raw 414-row table as a multimap;
2. admit a unigram-row glyph string as a one-letter atom;
3. admit every prefix-row plus suffix-row concatenation as a two-letter atom,
   except when the complete ciphertext string equals any unigram-row string,
   matching the encoder's `UNAMBIGUOUS=True` guard;
4. dynamically segment each complete source token into one or more atoms; and
5. deduplicate only identical complete plaintext-label streams.

This is a deck-agnostic support closure. It models deleted boundaries only
inside an observed source token and never joins across an observed source
space. It has no learned key, label permutation, exception budget, compound
cap, or language score.

## Dominance proof from the published H007 aggregate

The repair cannot meet an exact unique-stream gate:

1. Every H007 `BA` occurrence has no unigram match and has more than one
   distinct prefix-plus-suffix label pair under the published reverse maps.
2. The corresponding prefix and suffix rows necessarily exist in the raw
   forward table.
3. Because the complete token is absent from the unigram map, the encoder's
   `UNAMBIGUOUS=True` collision rule does not exclude either direct bigram
   construction.
4. The proposed closure retains both as one-atom parses.
5. Additional recursive segmentations can add outputs but cannot remove two
   already distinct complete label streams.

H007 reported 82 `BA` occurrences in the 2,341-occurrence discovery corpus.
At least those 82 occurrences must therefore remain ambiguous under the
deck-agnostic closure. This implication uses only H007's permitted aggregate
class count; no source token, token hash, label, folio outcome, or locus outcome
was opened.

## Table-only code audit

An independent standard-library reconstruction of the forward atom multimap
reproduced these immutable geometry facts:

- 18,947 distinct atomic ciphertext strings;
- 18,848 with one label stream, 95 with two, and 4 with three;
- 14,648 atomic strings also have a distinct decoding into two or more atoms;
- the shortest direct-versus-multi-atom collision is two ciphertext
  characters.

Thus arbitrary boundary deletion makes the published variable-length code
non-uniquely decodable even before manuscript text is considered. The
table-only assertions are retained in `tests/test_naibbe_coverage.py`.

## Exact boundary

Ignoring the shuffled 52-card deck and invisible collision retries
over-approximates forward support. A zero-path result would be an exact support
failure; multiple closure paths might theoretically be pruned by a fully
specified line-level deck history. The published reverse decoder does not know
that random history, however, and H007 supplies no shared deck order. The
closure therefore cannot authorize an unambiguous public-key reading.

Do not use the pinned Latin herbal controls to choose among these branches, to
repair the 495 H007 `X` occurrences, or to fit the 23 plaintext labels. That
would select fluency after seeing ciphertext rather than test a fixed decoding
mechanism. No implementation or manuscript run is warranted for this route.
