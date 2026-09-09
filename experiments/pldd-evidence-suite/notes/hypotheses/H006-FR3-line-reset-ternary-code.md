# H006-FR3-LINE: fixed three-trit line-reset code

Status: **frozen before any residue outcome under this exact protocol**

Protocol version: `H006-FR3-LINE-v1`

## Claim boundary

This is a key-independent necessary-condition screen for one narrow direct
decoding route. Matlach, Janečková, and Dostál propose that complex EVA signs
may expand into a smaller primitive alphabet and give an example in which each
plaintext letter is represented by exactly three digits from `{1,2,3}`, with
each digit written by a homophonous set of manuscript signs. They also mention
a new line, paragraph, or another resetting sequence as places where a broken
three-symbol frame might restart.

H006-FR3-LINE-v1 adds and freezes the restriction that **every physical prose
line starts at phase zero and resets independently**, with no padding, prefix,
tail, carry, deletion, insertion, or per-line phase choice. Under that
restriction, the expanded primitive-glyph count of every clean line must be
divisible by three regardless of the unknown glyph-to-trit key, plaintext
language, or A-to-Z code table. This invariant is tested before any key or
plaintext search.

A failure rejects only this project's conjunction of author-mentioned
component choices, fixed three-trit blocks, and independent line resets. It
does not reject a continuous book-wide frame, paragraph reset,
variable-length code, arbitrary codebook, Naibbe-like verbose cipher, or every
Matlach-inspired construction. A pass is only frame compatibility and cannot
license a plaintext character, word, or translation.

## Sources and historical scope

- Primary proposal: Matlach, Janečková, and Dostál, “The Voynich manuscript:
  Symbol roles revisited,” *PLOS ONE* 17(1): e0260948 (2022),
  <https://doi.org/10.1371/journal.pone.0260948>. Printable PDF retrieved
  2026-07-10, SHA-256
  `d4fd94df31e485422c88a07301cc2a6f92227858eadd484426aa9b6977172730`.
- The paper's S3 ligature-candidate figure was retrieved from
  <https://doi.org/10.1371/journal.pone.0260948.s003>, SHA-256
  `d54b5d581ffe57386d96f596aa1e2318961dfd3a12a35f9f0e1e9c07b87f3a7f`.
- Historical comparison: Somogyi, “Caratteristiche strutturali di cifrari
  monoalfabetici italiani nei secoli XIV e XV” (2016),
  <https://ojs.ppke.hu/verbum/article/view/405>, documents Italian homophonic
  systems near the parchment date, but not this fixed ternary construction.
  This is the title printed in the PDF; the landing-page metadata
  inconsistently says XV and XVI.
- Broader key survey: Megyesi et al., “Key Design in the Early Modern Era in
  Europe” (HistoCrypt 2021), <https://doi.org/10.3384/ecp183165>, likewise
  supports historical homophony and nulls, not a balanced or fixed three-trit
  Voynich key.

The ternary inspiration in Matlach et al. is attributed to a Trithemius method
disclosed around 1500, later than the parchment's 1404–1438 radiocarbon range.
H006 therefore treats this route as historically speculative.

Pinned manuscript inputs:

- ZL3b-n, extended EVA/IVTFF source of record, SHA-256
  `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc`.
- IT2a-n, historical Takahashi-derived EVA comparison, SHA-256
  `7f27a8b0feed8f6de0a99900df6bf912dd1d295c38e5f830bac8b41c3f536fb5`.

The analyzer must verify both byte hashes before parsing, require IVTFF
alphabets `Eva-` for ZL and `EvaT` for IT, and verify each parsed document
emits its input bytes unchanged. Any failure aborts before eligibility or
residue computation.

ZL and IT are correlated transcriptions of one manuscript, not independent
samples. GC2a uses the incompatible `v101` alphabet and may not be silently
projected through an EVA component table.

## Frozen line eligibility

The unit called a manuscript line below is exactly one parsed IVTFF logical
locus keyed by `(page_id, locus_number)`. A source-file continuation may span
multiple `PhysicalLine` records, but it remains one manuscript line and may
never be split into extra observations. Require exactly one ZL locus and one IT
locus at the key; a missing or duplicate witness excludes that key.

A line is eligible only when:

1. both loci are prose (`P*`) and neither locator is `!`;
2. ZL supplies Currier `$L` in `{A,B}`, hand `$H` in `{1,2,3,4,5}`, and
   illustration class `$I` in `{A,B,C,H,P,S,T,Z}`;
3. conservative Basic EVA tokenization finds at least one certain token in
   each witness and no uncertain space, alternative, unreadable glyph,
   Extended-EVA code, uppercase joined form, apostrophe, or unsupported
   symbol;
4. the complete ordered Basic EVA token tuple is byte-for-byte identical in
   ZL and IT; no disagreement is deleted or edited into consensus;
5. every glyph is in the frozen 19-sign inventory
   `{a,c,d,e,f,g,h,i,k,l,m,n,o,p,q,r,s,t,y}`; and
6. every `n` is word-final. Mid-word `n` invalidates the entire line rather
   than being repaired as a presumed scribal error; therefore `nn` is invalid
   because its first `n` is not final.

IVTFF `{...}` notation is admitted only when its contents are otherwise valid
Basic EVA: the braces explicitly mark a ligature *of the enclosed
Voynichese characters* in the IVTFF specification, so the delimiters are
removed and the enclosed ordered characters are retained. This is the same
documented normalization used by `tokenize_certain_basic_eva`; brace presence
is retained in the attrition audit, and no brace is counted as a glyph. A
braced/unbraced markup difference may therefore survive only when the complete
normalized character tuple still agrees. This is distinct from an uppercase
EVA joined form, which excludes the line.

Certain manuscript word spaces are removed before the frame test. No start,
end, or word-boundary marker enters the primitive stream. A page identifier
that does not match the physical-folio regex below is excluded rather than
assigned by hand.

Eligibility is the conjunction of all rules above. The audit records every
applicable exclusion reason for a key rather than assigning a single
precedence-dependent reason; a multiply invalid key may therefore contribute
to more than one attrition count, but never more than once to the eligible
inventory.

## Frozen component models

The paper warns that its component choices are heuristic, manually selected,
sometimes weak or disqualified, and possibly false positives. H006 pays for
exactly two project-instantiated variants assembled from author-mentioned
components and no others:

| Sign | `PAIR` expansion | `OPTIONAL_E` expansion |
|---|---|---|
| `d` | `ey` | `ey` |
| `f` | `id` | `ide` |
| `g` | `cd` | `cd` |
| `k` | `il` | `il` |
| `m` | `id` | `id` |
| `n` | `i` after removal of its following space component | same |
| `p` | `qd` | `qde` |
| `q` | `ie` | `ie` |
| `r` | `si` | `si` |
| `t` | `ql` | `ql` |

Expand recursively until only `{a,c,e,h,i,l,o,s,y}` remain. Thus, for example,
`PAIR` gives `d -> ey`, `q -> ie`, `f/m -> iey`, `p -> ieey`, `t -> iel`, and
`g -> cey`. `OPTIONAL_E` changes only the paper's suggested final-`e`
extensions on `f` and `p`. The visually mentioned `m -> il` alternative,
alternative `d` shapes, a special role for `o`, boundaries as a tenth trit,
and any newly invented decomposition are outside v1.

## Frozen physical-folio split

Derive the physical folio with strict regex `^(f\d+)[rv]\d*$`, so all sides
and panels of one leaf remain together. A folio is held out exactly when

`first_byte(SHA256("H006-FR3-LINE-v1:" + physical_folio_id)) < 51`.

Feasibility-only inventory, computed without any line-length residue:

- 1,185 eligible exact-consensus lines over 92 physical folios;
- discovery: 919 lines over 69 folios; Currier A/B = 332/587; hands
  1/2/3/5 = 332/357/214/16; illustration B/C/H/P/S/T =
  266/20/360/25/199/49;
- sealed holdout: 266 lines over 23 folios; Currier A/B = 171/95; hands
  1/2/3 = 155/20/91; illustration H/P/S = 161/14/91.

The split, eligibility, and component tables may not be altered after residue
inspection. Before any expansion, the analyzer must reproduce every frozen
inventory count above exactly; a mismatch aborts without computing a residue.

## Discovery-only frame screen

For each eligible discovery line and each component model, recursively expand
the complete line left-to-right and record `primitive_count mod 3`. Report the
full residue histogram overall and separately by Currier A/B, hand, and
illustration class.

This is a deterministic necessary-condition test, not a stochastic enrichment
test. Manuscript line lengths are structured and dependent, so an iid
binomial `p0=1/3` null would not be exact and is forbidden. Report contradiction
counts and proportions descriptively; do not attach a p-value.

Check discovery breadth before computing any model disposition. If it fails,
the result is `inconclusive` and held-out residues remain uncomputed. If it
passes, one component model qualifies on discovery only if all of these hold:

- discovery breadth: at least 800 lines over 60 physical folios, at least 300
  Currier A and 500 Currier B lines, and at least 300/300/150 lines from hands
  1/2/3;
- every eligible discovery line has residue zero. Equivalently, the overall
  zero-residue fraction is exactly 1.00 and every reported subgroup is also
  exactly 1.00.

One clean nonzero-residue line is a contradiction and kills that exact model.
There is no error-tolerant fallback, and no failing line may be located and
then dropped, padded, rephased, or repaired.

If neither model qualifies, reject H006-FR3-LINE-v1 immediately and do not
compute or report any held-out residue. If both qualify, lock the one with the
`PAIR` model. If exactly one qualifies, lock it.

## Sealed holdout and advancement

Only a discovery-qualified model authorizes evaluation of held-out residues.
Before evaluation, require at least 250 held-out lines over 20 physical folios,
at least 100/75 Currier A/B lines, at least 100/20/75 lines from hands 1/2/3,
and at least three illustration classes with ten lines each. A holdout breadth
failure is `inconclusive` and does not authorize held-out residue computation.

Every eligible held-out line must also have residue zero. Once authorized,
evaluate the locked model on the complete holdout and report its full aggregate
and subgroup histograms; do not stop at the first contradiction. One
contradiction rejects the locked model. A complete holdout pass would mark only
the line frame `promising` and authorize a separately frozen H006-FR3
key/plaintext stage. That later stage must exhaust all 18,150 labeled
surjective assignments of nine primitives to three nonempty trit classes,
treat codeword `333` as
invalid rather than inventing a null, retain a homophone trace for re-encoding,
validate on synthetic historical Latin/Italian controls, pay the full
key/language search in its null, and make locked full-line and semantic
predictions. It may not assume balanced 3/3/3 classes, because Matlach's
equal-size example is not a necessary rule.

No decoded string, language model, dictionary, word segmentation, or gloss may
be viewed or emitted by this frame stage.

## Pre-freeze contamination disclosure

Before this exact protocol was frozen, a parallel feasibility audit reported
an exploratory divisibility count on a different raw STA1 atomization. That
scratch screen used neither this EVA recursive expansion, this ZL/IT exact
consensus, nor this physical-folio split. It is contaminated, is not a test of
H006-FR3-LINE-v1, and may not set or retune any gate above. No residue under
the exact protocol in this file was inspected before freeze.

A separate pre-run protocol audit also removed an initially drafted
error-tolerant gate and iid-binomial calculation. That correction occurred
before any exact H006-FR3-LINE-v1 residue was computed. The deterministic
all-lines condition above is the only operative advancement rule.

A final pre-run acceptance audit made the brace normalization, logical-locus
unit, metadata domains, duplicate and foldout exclusions, illustration
inventory, and breadth-failure dispositions explicit. Those clarifications
also occurred before any exact residue was computed.
