# H002: local label-to-prose recurrence

Status: **within-ZL numeric screen met; exact-EVA crib not advanced after cross-transcription audit**

## Translation-oriented claim

If true diagram labels often encode the names or stable descriptors of their referents, exact certain-EVA label types should recur in running text on the same page more often than in running text on comparable pages. A positive result would prioritize label forms as noun/entity candidates; it would not reveal their meanings.

## Evaluation protocol

- Corpus: pinned ZL3b.
- Label subtypes: `La`, `Lc`, `Lf`, `Ln`, `Lp`, `Ls`, `Lt`, `Lz`. Exclude `L0` and extraneous `Lx`.
- Prose: `P*` loci on the same page.
- Tokens: certain basic EVA only. Use unique label types per page so repeated decorative labels do not dominate.
- Eligible page: at least one accepted label type, at least one accepted prose token, and at least one peer page with the same illustration type `$I`, Currier variety `$L`, and hand `$H`.
- Null for each label type: its prevalence in prose sets of all eligible peer pages in the same stratum, excluding its own page.
- Page score: observed local hit rate minus expected peer-page hit rate.
- Split by whole page using SHA-256 of `H002-v1:<page_id>` with the first byte below 51 held out.
- Primary criterion: positive aggregate enrichment in held-out pages, with at least ten evaluated label types. Report discovery and held-out page scores and raw counts.

## Interpretation boundary

Failure would reject exact same-page recurrence as a productive crib under this transcription/profile, not the general possibility that labels are noun-like. Success would identify forms for later blinded image tests but would not justify a gloss or phonetic value.

## Result

- Discovery: 23 pages, 279 evaluated label types, 30 local hits versus 28.3333 expected; enrichment 0.60%.
- Held out: two pages, 30 label types, two local hits versus zero expected; enrichment 6.67%.
- The frozen numeric criterion was met, but the independent evaluation unit is the page and the held-out breadth was only two pages. This is a descriptive within-ZL screen, not an inferential result.
- Both held-out hits were on `f89v2`: EVA `sheol` and `chody`.

## Independent-transcription audit

The finer GC2a/STA1 witness does not support exact member identity for either exact-EVA hit:

- ZL reads label `f89v2.5` and prose `f89v2.7` as `sheol`, both `L1J1A1B2`. GC reads the label as `LeJ1A3B2` but the prose occurrence as `L1J1A1B2`.
- ZL reads the second label word at `f89v2.12` and prose occurrences in `f89v2.9` as `chody`, `K1A1B1A2`. GC reads the label as `K1A1BaA2` while the prose form is `K1A1B1A2`.

The matches survive only at STA glyph-family level (`LJAB` and `KABA`), not at member level. The exact-EVA signal can therefore be produced by EVA's collapsing of distinctions that GC records.

Disposition: do not advance exact same-page EVA identity as a translation crib. Do not gloss `sheol` or `chody`. H003 retrospectively tests the looser family-level, locus-shared route over the corpus.
