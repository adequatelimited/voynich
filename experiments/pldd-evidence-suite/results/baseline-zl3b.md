# Voynich corpus baseline

> This is a transcription-structure report, not a decipherment or translation.

## Source integrity

- SHA-256: `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`
- Original source bytes retained: `true`
- IVTFF page/panel records / loci: 227 / 5385
- Locus families P/L/C/R: 4130/1029/84/142
- Paragraph starts / ends: 740 / 740
- Tokens with comma as boundary / joined: 39026 / 36278

## Conservative basic-EVA view

Accepted 32892 tokens of 7317 types. Excluded 3386 uncertain or extended components.

| Token | Count |
|---|---:|
| `daiin` | 783 |
| `chedy` | 445 |
| `shedy` | 380 |
| `ol` | 379 |
| `chol` | 331 |
| `aiin` | 315 |
| `qokeey` | 302 |
| `qokeedy` | 301 |
| `chey` | 292 |
| `dar` | 276 |
| `qokain` | 276 |
| `or` | 271 |
| `qokedy` | 270 |
| `qokaiin` | 263 |
| `ar` | 262 |
| `shey` | 233 |
| `okaiin` | 208 |
| `s` | 199 |
| `dain` | 194 |
| `chor` | 193 |

## H001: paragraph-initial positional enrichment

H001 tests only whether specific transcribed forms are enriched at paragraph starts. It assigns no meaning or phonetic value.

Discovery pages: 160; held-out pages: 47.

The literature-derived feature is an accepted basic-EVA token beginning with `k`, `t`, `p`, or `f` (the conventional gallows forms).

| Split | Initial feature rate | Background feature rate | Log2 odds |
|---|---:|---:|---:|
| Discovery | 82.50% | 5.25% | 6.403 |
| Held out | 92.96% | 5.63% | 7.723 |

The whole-token rows below are exploratory candidates, selected only in discovery with: discovery total>=20, initial>=3, log2_odds>=1.5. The frozen directional screen requires an observed held-out initial occurrence; smoothing alone does not count. This is descriptive, not inferential or an independent replication.

| EVA token | Discovery total | Discovery initial | Discovery log2 odds | Held-out total | Held-out initial | Held-out log2 odds | Positive held-out direction |
|---|---:|---:|---:|---:|---:|---:|:---:|
| `tchedy` | 26 | 10 | 4.854 | 5 | 0 | 2.075 | no |
| `pchedy` | 26 | 4 | 3.166 | 3 | 0 | 2.727 | no |
| `tar` | 22 | 3 | 3.007 | 6 | 0 | 1.834 | no |
| `tol` | 23 | 3 | 2.935 | 6 | 1 | 3.67 | yes |

Interpretation boundary: positional enrichment may reflect layout, scribal convention, morphology, a cipher mechanism, or grammar. It is not enough to gloss a token.

## H002: local label-to-prose recurrence

H002 tests whether exact certain-EVA types in true label loci recur in prose on the same page above a same-section, same-Currier, same-hand peer-page expectation.

| Split | Pages | Label types | Observed local hits | Expected peer hits | Enrichment |
|---|---:|---:|---:|---:|---:|
| Discovery | 23 | 279 | 30 | 28.3333 | 0.60% |
| Held out | 2 | 30 | 2 | 0.0 | 6.67% |

Primary criterion: held-out enrichment > 0 with at least 10 evaluated label types. Within-ZL numeric screen: met.

Held-out evaluation unit: page; count: 2. This is a descriptive within-ZL screen, not an inferential result. Independent-transcription validation is required before using any hit as a crib.

### H002 cross-transcription STA1 audit

The positional audit mapped 2 held-out EVA hits into both ZL and GC STA1. 0 retained exact member-level label/prose identity in both transcriptions; 2 retained family-level identity.

| EVA token | Exact member identity in both | Family identity in both |
|---|:---:|:---:|
| `chody` | no | yes |
| `sheol` | no | yes |

Neither exact-EVA hit is supported as an exact member-level recurrence by both transcriptions. Do not advance either as a translation crib. The looser family-level survival motivated the retrospective H003 screen below.

## H003: locus-shared family-level label recurrence

H003 retrospectively screens STA glyph-family types present in both ZL and GC at the same aligned locus. It uses unordered locus-level set intersection, not positional word agreement.

| Partition | Pages | Label types | Observed local hits | Expected peer hits | Enrichment |
|---|---:|---:|---:|---:|---:|
| Partition A | 20 | 215 | 48 | 43.0649 | 2.30% |
| Partition B | 6 | 62 | 15 | 13.5 | 2.42% |

Partition validity: retrospective exploratory partition defined after H002 output was inspected; partition B is not an untouched holdout.
All 6 partition-B pages with peers were already H002 discovery pages; 0 were untouched H002 held-out pages.

Frozen advancement criterion: partition-B enrichment>0, >=5 pages with peers, >=30 label types, and positive page scores > negative page scores.
Advancement result: not met. Disposition: do not advance this crib; absence is not established.
