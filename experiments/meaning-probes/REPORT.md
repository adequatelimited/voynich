# Meaning probes — results

Pass: `experiments/meaning-probes/`
Pre-registration: `PROTOCOL.md` (sha256 `26847ad7…`, frozen before any statistic was computed)
Primary transcription: ZL3b-n. Replication transcription: GC2a-n. Positive controls: Culpeper *Complete Herbal*, eight written numeral series.

---

## 1. Verdict

**Nothing passed. This pass establishes zero new verified word meanings — the running total for the project is unchanged.** Six pre-registered gates were run (Z1, Z2, Z3, Z4, R1, R2, L1). Five failed outright. One (R1's *ornamental* branch) turned out not to be measurable at all: the statistic it depends on has an invalid null and an unfrozen control-pool definition, so it can be reported neither as a pass nor as a fail. One sub-test (R1a, "paragraph openers are gallows-initial") passed its gate by an enormous margin, but the protocol assigns it no meaning claim on its own — it is a known fact about the manuscript, and the two tests that were supposed to decide what the opener *is* are the ones that failed or collapsed.

What **was** established, with measured power:

- The zodiac nymph labels are **not a written numeral system** of any kind that leaves material shared between neighbouring or corresponding numbers. Z1, Z2 and Z4 all return effects between 0.4 % and 3 % of what real numeral systems produce through the identical machinery, and the machinery detects real numeral systems at every ring size and slot layout tested. This is a well-powered negative, not an absent measurement.
- The labels are **not a fixed inventory**: 258 of 294 label strings are distinct (0.878), against a gate threshold of 0.50.
- The drawn stars in the Recipes section **do not index the text**: nothing survives Bonferroni, exactly as pre-registered, and the largest apparent effects are a page confound (`tail` is constant within page on 13 of 13 TEST pages).
- L1's name/grammar split **fails**: 2 of 25 word-final glyph units clear the gate where 3 are required, and — contrary to what the test agent reported — the positive control does clear the gate under the pre-registered estimator (4 of 25), so the failure is informative rather than an instrument failure.

The single durable positive observation in the whole pass sits **outside every frozen gate** and is therefore not claimed: label words are massively depleted in EVA `q`-initial forms relative to length-matched running text on the same page (merged `q`/`qok` log-odds −1.687; exact conditional P = 2.6 × 10⁻¹⁸ on TEST, 2.3 × 10⁻¹⁵ on FIT). This is long-standing Voynich folklore; what is new is only that it survives within-page, length-matched control.

Nothing here is transcription-replicated. The GC2a replication could not be run for any test, for a single mechanical reason given in §2.7.

---

## 2. What each gate did

### 2.1 Z1 — ordinal gradient inside a ring → **FAIL**

**Frozen gate.** Ordinal-like only if, on the TEST signs, (i) permutation p < 0.01 **and** (ii) Δ ≥ 25 % of the median Δ over the numeral controls at matched ring sizes. Report the fraction of numeral controls clearing p < 0.01 as measured power; below 0.5 the test is declared underpowered.

**Sample.** 10 rings on TEST (Leo r0/r1, Virgo r0/r1, Libra r0/r1, Scorpius r1/r2, Sagittarius r1/r2), sizes [18, 12, 18, 12, 18, 10, 16, 10, 16, 9], 139 labels, 957 pairs. Two rings of 4 labels dropped by the frozen ≥ 8 rule.

| statistic (TEST, glyph units, comma_split=True) | observed | p | gate |
|---|---|---|---|
| Δ = mean sim(g=1) − mean sim(g≥3) | **+0.00612** | 0.5616 | needs < 0.01 → **fail** |
| ρ̄ (mean per-ring Spearman, gap vs similarity) | **−0.00280** | 0.9338 | needs < 0.01 → **fail** |
| mean sim at g=1 vs g≥3 | 0.2215 vs 0.2154 | — | — |
| Δ as fraction of numeral-control median (0.15396) | **3.98 %** raw, **8.5 %** bias-corrected | — | needs ≥ 25 % → **fail** |

The bias correction is the null-correctness verifier's. The pooled Δ has a non-zero H0 expectation (E[Δ | H0] = −0.00407 analytically, −0.00423 simulated) because the g=1 and g≥3 buckets weight rings differently; correcting both sides gives Voynich +0.01019 against a numeral median of 0.12004, i.e. **8.5 %**, not 4 %. The gate fails by a factor of three either way. Quoting the raw 3.98 % without the correction slightly overstates how small the effect is.

**Numeral controls at matched ring sizes** — English +0.1224, Latin +0.1632, Italian +0.1623, German +0.1197, French +0.1076, Roman +0.2484, Greek Milesian +0.1456, `d`+Roman +0.1754; every p = 0.0001. The Voynich value is 4–40× smaller and non-significant.

**Negative controls** at the same ring sizes: 30 Culpeper headings +0.0232, 30 Vulgate word types +0.0347, 30 herbal label words −0.0111. **The Voynich Δ is smaller than two of the three no-structure controls.**

**Measured power.** The pre-registered figure is 8/8 = 1.00, and the protocol's underpowered branch does not fire. But that figure is inflated and should not be the headline: `cut_cyclic` at these ring sizes produces only **7 distinct rings out of 10** (the 18-label ring is reused three times, the 12-label ring twice), which narrows the control's permutation null. Both the null-correctness and confound verifiers independently replaced it with a construction-free statement, derived directly at the observed Voynich ring configuration where the permutation null is ordering-independent:

> **The smallest Δ this design can detect at p < 0.01 is +0.042** (null-correctness: +0.04207 at 20,000 draws; confound: +0.04252). That is **27–28 % of the numeral-control median**. All eight numeral systems sit at 2.6×–5.9× that floor. The observed Voynich Δ is **0.15×** it.

Two limits on that power, both from the confound lens and both to be carried forward: power **at the gate's own 25 % bar** is 0.42, not 1.00 (the detection floor sits marginally above the effect-size bar, so the two gate conditions are not independent — the same construction is used by Z2); and under dilution, a numeral system covering under about half the labels in a ring would have been missed (detection 0.00 at 10 % coverage, 0.15 at 30 %, 0.40 at 50 %, 1.00 only at 70 %).

**Type-I calibration.** 400 H0-true datasets at the real ring configuration: P(p ≤ 0.01) = 0.0050 against nominal 0.01. The test is correctly calibrated, if anything conservative.

**Ambiguity readings taken.** Gap is linear |i − j| with no wrap-around; `PROTOCOL.md` does not specify this, and the linear reading is the harder one (the circular reading is more favourable to the ordinal hypothesis). The circular arm was run and is also null: Δ = +0.00548 p = 0.554, ρ̄ = −0.0444 p = 0.2104, ratio 4.13 %, controls still detected 8/8. Both statistics were required at p < 0.01 (harder reading); the lax "either one" reading also fails. Gate (ii) used the larger of the two control medians (harder threshold); the smaller gives 6.1 %, still far under 25 %.

**Replication.** Not run and not required (only passing gates replicate). Not runnable either: see §2.7.

---

### 2.2 Z2 — same slot across signs → **FAIL**

**Frozen gate.** p < 0.01 on TEST under at least one of the three slot conventions **and** effect ≥ 25 % of the numeral controls' effect under the same convention.

| convention (TEST, glyph units) | effect | p (two-sided) | control median | ratio | gate |
|---|---|---|---|---|---|
| A — index within sign | −0.00498 | 0.6422 | +0.6664 | −0.007 | fail |
| B — index within ring, outer-first | −0.00704 | 0.5972 | +0.6707 | −0.011 | fail |
| C — clock rounded to 30 min | +0.01601 | 0.1095 | +0.6907 | 0.023 | fail |
| C, raw EVA characters (robustness) | +0.02140 | **0.026–0.033** | +0.6686 | 0.032 | fail |

The C/char p is quoted as a range because two verifiers moved it in opposite directions and neither is wrong: recentring the two-sided p on the (non-zero) null mean gives 0.026; banker's rather than half-up rounding of the 15-minute ties gives 0.0281; the ring-preserving null gives 0.033. Every version is at least 2.6× short of the 0.01 gate and ~8× short of the effect bar. The same convention on the FIT half is **negative** (−0.00808). It is not a result and is recorded only so nobody later mistakes it for a suppressed signal. Across the 12 reported cells, and across the ~40 cells the verifiers added, no cell survives any multiplicity correction.

**Measured power — restated.** The pre-registered "power = 1.00" (8/8 numeral series at p < 0.01 under every convention, and 8/8 again with 30 % of items corrupted) is arithmetically correct but describes a straw control: the synthetic numerals are byte-identical at the same slot in every sign. Two verifier constructions give a far better statement of the same fact:

- **Implantation floor (confound lens).** Overwriting real TEST labels so that a fraction carries genuine same-slot correspondence — keeping the manuscript's own vocabulary, lengths and 0.21 similarity floor — fires at **10 of 147 labels** (convention A, effect +0.033, p = 0.0025) and at 7 labels under convention C. The detection floor is about **5 % of labels**. The manuscript shows nothing at that level or above.
- **Degradation sweep (null-correctness lens).** The p-arm detects a numeral layout up to roughly **80–85 % item corruption** and goes blind beyond it; the 25 %-effect arm already fails at 50 % corruption. The observed Voynich effect lies inside the blind region of the p-arm — which is precisely what the effect bar exists to exclude.

**Rotation was the one alignment gap the three frozen conventions leave open, and it is also null.** A rotation-invariant statistic (best cyclic offset per sign pair, own max-statistic null) gives z = +0.01 (p = 0.484) on TEST. Per-sign numbering start offsets are now ruled out, not merely untested.

**Corrections applied.** Convention B's numeral control wraps a 30-item series over 44 distinct slot values, so 14 of 44 slots carry a duplicate numeral; this deflates B's control effect and therefore *lowers* B's 25 % bar slightly below what the protocol intends. B's observed effect is negative, so nothing turns on it.

---

### 2.3 Z3 — inventory → **FAIL**

**Frozen gate.** "Fixed inventory" asserted only if distinct/total < 0.50.

| quantity | value |
|---|---|
| distinct label strings / label loci | **258 / 294 = 0.8776** → fail, by a wide margin |
| label word types / tokens | 277 / 344, TTR 0.805 |
| strings repeating at all | 27; shared by ≥ 2 signs 24; by ≥ 3 signs 4; within one sign only 3; max repeat 5 (`otaly`) |
| within-sign distinct/total | 0.931–1.000 per sign |

Most repeats are cross-sign, and within-sign repetition is essentially nil — the opposite of what a per-sign numeral restart predicts (~0.10). The figure is a *floor* on distinctness: a locus whose illegible token was dropped can only collide with another locus, so the true distinctness is at least this high. No parser, ordering or pooling choice moves 0.878 below 0.50. Replicates on GC2a at 78/91 = 0.857, the one GC2a number worth anything (a thinned sample can only make distinct/total look lower).

**Two Z3 side-findings are withdrawn**, both on verifier objections graded material:

1. **"Labels use a strict subset of the running-text glyph inventory" (38 vs 40 units, 0 label-only, 2 text-only) — withdrawn.** Rarefying the 947 running-text tokens down to 344 gives a mean of 38.00 distinct units (sd 1.08) and misses on average 2.01 of the full inventory. The observed numbers are the dead-centre expectation for a sample of that size. The defensible statement is "labels and running text draw on the same ~40-unit inventory."
2. **"Labels are significantly more lexically varied than length-matched running text (0.805 vs 0.661, z = +8.19, p = 0.0020)" — withdrawn as reported.** The resampling null drew *with replacement* from tiny per-(page, length) cells (median ~15 tokens; 5 cells have more label targets than the pool has tokens), manufacturing collisions and deflating the null TTR. Without replacement, the harder and equally literal reading: null mean 0.7675, **z = +2.49, two-sided p = 0.014**. Under the label/text retag exchangeability null that the protocol itself prescribes for the analogous L1 contrast, the **sign reverses** (null mean 0.8224, z = −1.07, p = 0.30). A third verifier reproduces the direction at z = +7.01 with frequency skew removed and notes the z ranges +5.1 to +8.3 across matching rules. The direction is probably real; the magnitude is not stable, this was never a gate, and it should not be cited at z = +8.19.

---

### 2.4 Z4 — positional morphology → **FAIL** (JSON records `PASS`; see erratum)

**Frozen gate.** Any MI with permutation p < 0.01 after Bonferroni over the four position × form combinations is reported as positional structure. Otherwise: none.

Five of the six statistics the test ran are flat or negative. One clears its threshold. **That one does not survive adversarial review, and Z4 is reported as a failure.**

| statistic (TEST, glyph units) | debiased effect | p | numeral median | systems detected |
|---|---|---|---|---|
| MI(rank block; first unit) | **+0.0027 bits** | 0.9223 | +0.7091 bits | 6/8 |
| MI(rank block; last unit) | **−0.0281 bits** | 0.4113 | +0.2507 bits | 5/8 |
| χ²(prefix inventory × rank block) | **+0.195** | 0.9683 | +120.5 | 6/8 |
| χ²(suffix inventory × rank block) | **−3.657** | 0.5319 | +43.3 | 5/8 |
| MI(ring third; last unit) | +0.0509 bits | 0.1193 | +0.2073 bits | 5/8 |
| MI(ring third; first unit) — the passer | +0.0975 bits | 0.00160 | +0.0964 bits | **3/8** |

(Control medians corrected by the null-correctness lens: the test reported `sorted[len//2]` of 8 values, which is the upper middle order statistic, not the median. The corrections are small but they matter for one framing — on the ring-third/first-unit axis the manuscript's +0.0975 bits is **101 %** of the true numeral median, not 86 %.)

**The four rank-block statistics are the axis on which a compositional numeral system — a tens morpheme at the front, an ordinal suffix at the back — must light up.** The test detects 5–6 of 8 real numeral systems there. The manuscript returns +0.0027 bits, −0.0281 bits, +0.195 and −3.657, with p = 0.92, 0.41, 0.97, 0.53. That negative is confirmed by all three verifiers under independent reimplementation and is the whole of what Z4 established.

**Why the sixth statistic is not a finding.** The confound lens graded this fatal, and I take that grading:

- *"Thirds of the ring" is unfrozen where it bites.* Eight of the twelve TEST rings have sizes not divisible by 3 (4, 4, 9, 10, 10, 12, 12, 16, 16, 18, 18, 18), so an analyst must decide where the remainder label goes. `t_z4` uses `floor(3i/s)`, putting it in the first third. `PROTOCOL.md` registers no such rule. **floor → p = 0.0013 (pass); midpoint → p = 0.0242; ceil → p = 0.0354.** Only 12 of 147 labels (8.2 %) change third between floor and ceil, and that relabelling moves p by a factor of 27. This is not a sensitivity difference between conventions: all three detect the numeral positive controls equally (3/8, 3/8, 4/8).
- *"Thirds of the ring" was implemented as thirds of the transcription's label list, not of the ring.* ZL records a clock position for all 147 TEST labels and the rings are not evenly spaced. The ring-relative **angular** third gives p = 0.0099; the absolute dial third gives a **negative** effect at p = 0.597.
- *The effect exists at exactly k = 3 blocks and nowhere else, and k = 3 is the least sensitive choice.* k = 2: p = 0.309 (numerals 4/8); k = 3: p = 0.0013 (numerals 3/8); k = 4: p = 0.462 (numerals **6/8**); k = 6: p = 0.238 (numerals **7/8**). The manuscript is flat on both of the partitions that are twice as sensitive to a real numeral system.
- *It exists only at the frozen 20-merge grain.* Raw first EVA character p = 0.0826 (this is the protocol's own registered robustness check, and it fails); first 2 characters p = 0.0396; first 3 characters p = 0.0067.
- *It fails every split.* FIT signs p = 0.497. Leave-one-sign-out at matched n: 0.0002 (drop Leo) to 0.052 (drop Virgo) — only 1 of 5 subsets clears even the lenient threshold. Leave-one-ring-out: 3 of 12 clear.
- *What the pattern actually is.* No label in the first three slots of any of the twelve rings begins with the glyph unit `y` (0/36, vs 19/111 later; `y` by third 1/53, 8/47, 10/47). A ring "begins" at the Lz locus whose ZL position character is `@` — the transcriber's mark for where he started reading the circle. The floor convention is exactly the one that widens that opening block. `y` was selected after seeing the table, out of 8 testable prefix types, and does not clear a Bonferroni correction over those 8 (its one-vs-rest p is 0.0031 against a 0.00125 bar).
- *And its p is a coin flip.* The true permutation tail probability is q = 0.001655 (95 % CI 0.001529–0.001781, from 400,000 draws, 200,000 on streams independent of the run's own), straddling the 0.0016667 threshold. The expected reported p under the registered procedure is 0.001755 — a failure. **P(the registered B = 10,000 procedure declares this a pass) = 0.413.**

**Two undisclosed departures from the pre-registration**, both recorded here because they are load-bearing for how the number was framed rather than for the verdict:

1. `PROTOCOL.md` fixes seed 408; `t_z4.py:342` runs the ring-third family at seed 409 (`seed + 1`). At the registered seed the same statistic gives p = 0.00090.
2. `PROTOCOL.md` registers Bonferroni over **four** combinations (α = 0.0025); the run used **six** (α = 0.0016667) after adding two χ² tests the protocol never registers — two of which are computed on the same contingency tables as two of the MI members. Under the registered family the statistic would pass stably (P ≈ 0.97 over seeds).

I take the harder six-member reading, as the working rules require. But note that the fatal objection does not depend on it: **midpoint (0.024), ceil (0.035) and the angular reading (0.0099) all fail the lenient 0.0025 threshold too, by an order of magnitude.** The convention confound kills the finding under either family size.

Two smaller corrections to the record: the test's own high-precision B = 200,000 rerun reuses seed 409 and therefore contains the gated draws verbatim — it cannot corroborate them (independent streams give 0.001670, on the failing side); and the "6 of 10 alternative seeds clear it" figure is really 5 of 9, since seed 409 in that list *is* the registered stream (20 of 40 across a wider sweep).

> **Erratum for `results/z4.json`.** The file records `gate.outcome = "PASS"`. That value is superseded by this report: Z4 is FAIL / no claim. The JSON was not edited; downstream readers should treat this section as authoritative.

**Replication.** GC2a TEST p = 0.566 on the same statistic, on 26 surviving labels that do not span more than one rank block. Not evidence in either direction — see §2.7.

---

### 2.5 R1 — the paragraph opener

#### R1(a) gallows rate → **PASS**, and stronger than reported

**Frozen gate component.** (a) must exceed the control by ≥ 3 SD.

| | TEST (even Recipes-B folios) |
|---|---|
| paragraph openers beginning with a gallows | **0.8955** (n = 134; `p` 70, `t` 35, `k` 9, `f` 6, none 14) |
| paragraph-internal line-initial words | 0.0553 (n = 380) |
| all Recipes words | 0.0783 (n = 5,056) |
| difference vs line-initial | +0.8403, **18.9 SD**, p at the 10⁻⁴ permutation floor |
| difference vs all words | +0.8172, 35.3 SD (label-permutation null: 31.1 SD) |

The confound lens tightened this rather than weakening it: against a **length-matched** null drawn from same-length section tokens the openers sit at **31.8 SD** on TEST, 30.7 on FIT, 43.9 pooled; against same-length line-initial tokens, 40.9 / 46.0 / 57.7. Openers are longer than controls (6.78 vs 5.25 EVA chars) but the gallows rate is flat in length across the section, so length is not the driver. Scribe, section and Currier language are constant across the stratum ($H=4 on all 11 TEST pages), the parser drops the first raw token on 3 of 285 paragraph-start loci vs 7 of 799 internal-line-start loci (no positional bias), and R1 never touches the 20-merge list. Paragraph identity is fixed by the star drawn in the margin, not by the text, so (a) is not circular with the opener glyph.

**This passes its gate and licenses no meaning claim.** That paragraphs open with gallows is already known; the protocol assigns the interpretation to (b) and (c).

#### R1(b) ornament test → **NOT MEASURABLE.** No ornamental claim, and the reported reversal is withdrawn.

**Frozen gate component.** *Ornamental initial* is asserted if (b) shows the residue attested at a rate indistinguishable from or above the matched control (two-sided p > 0.05) **and** (a) exceeds the control by ≥ 3 SD.

As executed, (b) reported p = 1.0000 on TEST (0.6413 vs 0.6430) and therefore a formal pass, with a supplementary relaxed-matching run reversing it to −3.56 SD, p = 0.0008. **Both numbers are dead.** Two verifiers graded this fatal, on independent grounds, and the third graded the reversal material:

1. **The null does not control type-I error.** It is not a permutation null: for each opener it draws one control *with replacement* from that opener's own (gallows, length) cell and treats the cell's empirical composition as the population truth. Cells are tiny — on the pooled section 18 of 242 matched openers draw from a cell containing exactly **one** control token; 22 more from a cell of 6; 47 from a cell of 11. A one-token cell contributes zero variance while asserting that token's attestation status for 18 openers. Measured on H0-true data using the script's own procedure: **nominal α = 0.05 rejects at 0.352; α = 0.01 rejects at 0.228; α = 0.001 rejects at 0.1175.** Null-z has SD 2.1–2.5 instead of 1.0. Every rejection in (b) and (c) is void.
2. **Under the correct null, nothing rejects anywhere.** Recomputed with the conditionally-exact within-cell label permutation (Cochran–Mantel–Haenszel conditional inference), same matching, same 10,000 draws:

| stratum | as run | corrected |
|---|---|---|
| TEST exact (pre-registered) | −0.04 SD, p = 1.0000 | +0.41 SD, p = 0.717 |
| TEST relaxed (no opener dropped) | −3.56 SD, p = 0.0008 | −0.26 SD, p = 0.861 |
| FIT exact | −3.17 SD, p = 0.0024 | −0.32 SD, p = 0.871 |
| FIT relaxed | −3.63 SD, p = 0.0006 | −0.56 SD, p = 0.631 |
| pooled Recipes-B exact | −2.96 SD, p = 0.0033 | +0.21 SD, p = 0.905 |
| pooled Recipes-B relaxed | −3.58 SD, p = 0.0006 | +0.09 SD, p = 1.000 |
| Herbal (all) exact | −1.71 SD, p = 0.0882 | −0.96 SD, p = 0.370 |

3. **The −3.56 SD reversal was a degenerate comparison even before the null is corrected.** All of it comes from the 28 TEST openers exact matching could not pair: their relaxed "control" is attested at 0.985 against a section-wide gallows control rate of 0.64, because 21 of 28 relaxed buckets contain fewer than 5 distinct control words (17 contain exactly 2, one exactly 1) — eighteen length-9/10 `p`-openers all matched to the same 2-word length-8 bucket. Attestation falls steeply with length (pooled: 0.921 at length 3, 0.508 at 7, 0.200 at 9) and the substitute controls are 1–3 characters *shorter* than the openers they stand in for. Forbid the substitute to be shorter and the reversal disappears entirely: **−0.03 SD, p = 1.0000.**
4. **The control-pool composition is not frozen, and it — not the openers — decides the answer.** `PROTOCOL.md` fixes the matching variables (gallows character, word length) but never says which pages control words come from, whether they are drawn by token or by type, or what happens when no control of the opener's length exists. Same statistic, same pre-registered exact matching, only pool scope changed: **TEST goes from −0.04 SD (own half) to −3.51 SD, p = 0.0004 (whole section, and this version drops only 4 openers, not 28); FIT goes from −3.18 SD (own half) to −0.77 SD, p = 0.473 (whole section) with the opener set identical.** Across seven admissible variants TEST spans −3.51 to +0.75 SD and FIT spans −3.18 to +0.70 SD, and the halves are **anti-correlated**: every variant that makes one half significant makes the other null. In no variant do both halves reject in the same direction at p < 0.05.
5. **A frequency confound runs through all of it.** The control is drawn from token positions and is therefore frequency-weighted, while openers are one per paragraph and systematically rarer words (mean log₂ section frequency: openers 0.664 vs control 0.882 pooled, −3.6 SD). Drawing controls by *type* collapses the pooled effect from −2.99 SD to −0.99 SD (p = 0.361) and flips FIT positive.
6. **The null carries no page-level variance component** while per-page opener attestation runs 0.00 (f116r) to 1.00 (f112r), so every (b) p-value — the test's and the verifiers' — is anti-conservative. Matching each opener to a control on its own page weakens every stratum (TEST p = 0.172, FIT p = 0.096, pooled p = 0.016) at the cost of dropping over half the openers.

**Consequence.** The *ornamental* branch is neither asserted nor refuted. The honest statement is: **the pre-registered (b) statistic is not identified.** Under the corrected null the point estimates sit within 0.3–1.1 SD of their controls in all six strata, which is consistent with the ornamental reading and inconsistent with nothing; but a non-rejection from an unidentified design under an unfrozen control-pool definition is not a gate pass, and the protocol's own harder-reading rule (a non-rejection gate is made harder by whichever admissible reading rejects) was not applied to the pool-scope ambiguity. The 28 unmatchable openers remain a genuine, reportable **coverage limit** of the frozen design — paragraph openers are systematically longer than gallows-initial non-initial words, and for lengths 9–11 no matching control exists in the section — but they no longer support a directional finding.

Also withdrawn: the (c) entropy comparison at "−692.9 SD" (pooled) and "−357.8 SD" (Herbal). Control SD 7.2 × 10⁻⁵ / 1.1 × 10⁻⁴ reflects a control distribution pinned to a single value (the winning control type was `pshedaiin` in 1,998 of 2,000 draws). A z of −693 is a diagnostic that the null has collapsed, not a measurement.

#### R1(c) lexical opener → **FAIL**, decisively and unconfoundably

**Frozen gate component.** Asserted only if one word type, or one stripped-residue type, accounts for ≥ 10 % of paragraph openers with permutation p < 0.01.

| | TEST |
|---|---|
| commonest opener type | `tchedy`, **4 / 134 = 2.99 %** (the 4.35 % figure reported elsewhere is 4/92, over the exact-matched subset only — the protocol's denominator is the 134 openers) |
| commonest stripped residue | `chedy`, 5 / 92 = 5.43 % |
| one-sided p | 1.0000 — the observed share is *below* the matched control (8.12 %) |
| Herbal (all), commonest opener type | `tchor`, 1.9 % |

The gate is an absolute threshold on a count. No parser, matching or pooling choice closes a factor-of-three gap. Openers are more diverse than the control, not less. **There is no *Item* / *Take* formula in the Recipes section.**

---

### 2.6 R2 — do the drawn stars index the text? → **FAIL (nothing survives), as registered**

**Frozen gate.** Report anything surviving Bonferroni p < 0.01 over the 53 tests. Registered expectation: nothing survives.

| | TEST (even Recipes folios) |
|---|---|
| star-annotated paragraphs | 130 (of 271 in the section) |
| tests actually run | 156 (3 predictors × 52 outcomes) |
| Bonferroni threshold, 156 tests | 6.41 × 10⁻⁵ |
| Bonferroni threshold, protocol's "53" | 1.89 × 10⁻⁴ |
| survivors, either threshold | **0** |
| uncorrected p < 0.05 | 10, against 7.8 expected by chance |

The R2 machinery was verified clean by two lenses (χ² reproduces exactly; the free-permutation null is the pre-registered one and correctly implemented; the largest effect recomputes to p = 0.0008 on an independent seed against 0.0005).

Two things must be stated rather than buried:

- **`tail` is a page property, not a star property.** All 13 TEST pages are all-or-nothing for it (Cramér V with page identity = 1.000), and the ZL comments are per-page boilerplate — "Light star, 7 points, tail" repeated verbatim down f104r–f115v. Every `tail` test under the registered free permutation is testing whether Voynich vocabulary is page-clustered, which it is. The supplementary "page-stratified null gives p = 1.0000" is restated: **a within-page shuffle of a within-page constant has exactly one realisation and carries no information at all.** The design cannot separate `tail` from page identity, so the 52 `tail` tests per stratum are structurally uninformative, leaving only `dotted` and point-count as real tests. Note also that 2 of the 8 no-tail TEST paragraphs are on f58r, which is Currier language A, so the contrast is partly a language contrast. This does not threaten the negative result: the registered null is *anti-conservative* for a page-clustered predictor, so non-survival under it is safe.
- **A structural power ceiling.** Under the harder reading (Bonferroni over the 156 tests actually run) the threshold 6.41 × 10⁻⁵ lies **below** the 10,000-draw permutation p floor of 1/10,001 = 1.0 × 10⁻⁴, so no test *can* be declared a survivor at the registered number of draws. Under the protocol's literal "53 tests" the threshold is attainable and no TEST-stratum test reached it. The FIT half has 1 test below the protocol-53 threshold and the pooled section 3 — every one a `tail` test, and every one collapsing under the page-stratified null (p = 0.20–0.99).

Also recorded: `parse_star` coerces the transcriber's own uncertainty to definite values (`tail?` → True, `7? points` → 7, `7/8 points` → 7); 16 of 271 star comments carry an explicit `?`, and 18 of 292 Recipes paragraphs carry no comment and are silently absent. Both are attenuating, so neither can manufacture a null, but both lower the stated power further.

---

### 2.7 L1 — label register vs running text → **FAIL**, against a *calibrated* control

**Frozen gate.** A name/grammar split is asserted if ≥ 3 of the 25 frozen word-final glyph units show |log-odds| ≥ 1 with permutation p < 0.01 after Bonferroni over K = 25, **and** the pooled effect is ≥ 25 % of the Culpeper control's.

| leg | value | gate |
|---|---|---|
| leg 1 — units passing, TEST (odd folios), word-final | **2 of 25** | needs ≥ 3 → **fail** |
| leg 2 — pooled mean \|MH log-odds\| 0.6462 vs control 0.6497 | ratio 0.994 raw; **0.82** null-corrected; **0.755** like-for-like at character level | needs ≥ 0.25 → pass |

**Sample.** TEST: 466 of 472 label words vs 3,098 text words in 109 (page × glyph-unit-length) strata across **25** pages contributing informative strata (the "26 pages" figure is the count of odd folios carrying both registers). FIT: 529/536 vs 3,203 in 126 strata across 28 pages. Control: 1,359 Culpeper heading words vs 56,938 body words in 1,134 strata over 525 entries.

**The headline correction, from the reimplementation lens and visible in the test's own JSON.** The test reported that the positive control clears leg 1 for only 1 of 25 units and concluded that "the control fails the same gate, so the failure carries no evidence either way". That is true only under a continuity correction the protocol never registers. Under the **pre-registered plain Mantel–Haenszel log-odds** — `PROTOCOL.md` says "within-page log-odds ratio label vs. text, pooled Mantel–Haenszel style" and registers no correction — the control clears **4 of 25** (`r` +1.129, `o` −1.523, `g` −1.220, `p` +1.657, all Bonferroni p = 0.0025). Four ≥ three: **the control passes leg 1.** The number is recorded in `results/l1.json` as `culpeper_control.final.n_units_passing_uncorrected_estimator = 4` and was simply left out of the gate block and the narrative. Correspondingly, `control_units_passing_initial` is **2** (corrected) or **4** (uncorrected), not the 0 that was reported.

**So the gate is calibrated and L1's FAIL is an informative negative result, not an instrument failure.** The manuscript clears 2 of 25 where the control clears 4.

**Estimator sensitivity, disclosed.** The continuity constant is an unregistered free parameter chosen in-script with the strata in view. Across five defensible conventions on one shared permutation stream: κ = 0.5 → 3 units (`daiin`, `eey`, `n`) and the gate would **pass**; κ = 1.0 (used) → 2, fail; κ = 2.0 → 1, fail; flat Haldane–Anscombe +0.5 → 1, fail; **uncorrected (the pre-registered reading) → 2, fail**. FAIL is the outcome under four of five conventions, including the protocol-literal one and the harder-reading rule. It is one knob from a pass, and that must be on the record.

**Neither of the two word-final passers survives.**

| unit | as reported | what happened |
|---|---|---|
| `n` final (7 label / 1 text word) | +1.586, Bonferroni p = 0.0025 | Under the **pre-registered uncorrected** estimator, p = 0.121 — not significant by any margin. Under an unconditional register-swap placebo null, p = 0.0246. Leave-one-out on any one of the 7 label words puts Bonferroni p at 0.012–0.037. The string `dan` appears on both sides (label on f71v/f89r1, text on f11v/f49v); only the page decides its register. **Not a result.** |
| `daiin` final (4 label / 95 text) | −1.102, Bonferroni p = 0.0050 | The text register's TTR is 0.366 against the labels' 0.786 and `daiin` is the single most frequent text token (121 tokens on 26 TEST pages). Deduplicating both registers to types within page: **−0.612, Bonferroni p = 0.607.** Page-hapax text: −0.559. And as a *genuine suffix* (words of glyph-unit length ≥ 2, so `daiin` is not simultaneously its own first and last unit): **−0.676, p = 0.13.** **Not a result.** |

Under the pre-registered estimator the two passers would instead be `daiin` (−1.629) and `eey` (−1.394), both negative and both in the direction L1 predicts — a more coherent pair, but `daiin` dissolves for the reason above and `eey` alone is not 3 units.

**The word-initial family (added by the test, not pre-registered) reduces to one fact.** Four units were reported as passing on TEST; two do not survive:

- `c-` (1 label / 64 text, −1.496): **refuted as a position artefact.** A label locus is structurally locus-initial; running text also has locus-medial positions. Of 491 locus-initial text words on TEST pages, **zero** begin with the bare unit `c` (benched gallows `cth/ckh/cph/cfh`, or `c` not followed by `h`), against 87 of 4,072 text words overall. Under a symmetric locus-initial design the sign flips to +1.095. On the FIT half it is −0.350, Bonferroni p = 1.000.
- `daiin-` (2 label / 60 text, −1.549): **refuted.** 121 of the 122 text tokens with `daiin` as first unit are the bare one-unit word `daiin`. Restricted to words where it is genuinely a prefix (length ≥ 2): 0 label / 1 text token in one stratum — nothing. Type-level: −0.567, p = 1.000; on FIT at type level it **reverses** to +0.495.
- `q-` and `qok-` are **one phenomenon counted as two units** (every word in both begins with EVA `q`). Merged into a single binary test: **log-odds −1.687, permutation p = 0.0001, exact conditional P(T ≤ 6 | E = 47.61) = 2.6 × 10⁻¹⁸ on TEST and 2.3 × 10⁻¹⁵ on FIT.** It survives every control applied to it: type-level dedupe, page-hapax text, character-length strata, dropping the six biological pages that supply most `qok-` text tokens, dropping the zodiac/astro/cosmo nymph-label pages, text restricted to paragraph loci, the symmetric locus-initial position control, the FIT half, and leave-one-page-out (|log-odds| never below 1.51).

The comparative framing of that family is also corrected: manuscript 4 units vs control 2 (or 4 uncorrected), not 4 vs 0; and **at matched measurement level the control out-detects the manuscript** (manuscript at raw EVA character level 0 word-final / 1 word-initial unit, against control 1 / 2). The claim that the word-initial comparison "is not power-limited in the manuscript's disfavour" is withdrawn.

**Leg 2 is a noise-floor comparison.** The manuscript's 0.6462 sits on a null floor of 0.3168 (permutation) / 0.3660 (placebo); Culpeper's 0.6497 on 0.2459. Excess-over-null ratio **0.816**, not 0.994. Separately, the manuscript is measured at glyph-unit level against a **character**-level control, so a unit like `chedy` is being compared with an English final `e`; like-for-like at character level the ratio is **0.755** (word-final) and **0.842** (word-initial, against the reported 1.888). Leg 2 passes under all of these, so the verdict is unaffected — but 0.994 and 1.888 should not be quoted as clean effect comparisons. Relatedly, under a register-free placebo the word-final family already produces a median of 3 units with |log-odds| ≥ 1 (95th pct 5), so the magnitude leg has teeth only in conjunction with the p leg.

> **Errata for `results/l1.json`.** The `estimator` string says "Haldane–Anscombe corrected (0.5 added to every cell of every stratum)". The code implements a *marginal proportional* correction with κ = 1 on informative strata only, and its own comment argues against flat Haldane–Anscombe. Under the estimator the JSON describes, leg 1 gives 1 unit rather than 2 and the word-initial family collapses from 4 passers to 1. Also: "26 pages" → 25 informative.

**Standing limitation, untestable in this pass.** The label side is defined entirely by Zandbergen–Landini's editorial locus-type letter `L`. If that assignment was influenced at the margin by how label-like a string looked, rather than purely by layout position beside a drawing, the whole L1 contrast is partly circular. No data in this pass can test it.

---

### 2.8 Replication on GC2a — not runnable for any test

Every test recorded GC2a numbers; **none of them is evidence in either direction**, for one mechanical reason. GC2a-n is Glen Claston's v101-family transcription, in which digits and upper-case letters are glyphs. The frozen `clean_tokens` keeps only `[a-z]+` tokens and drops anything containing a digit, so the surviving subset is the digit-free tail, not a random sample.

| test | ZL3b retention | GC2a retention | consequence |
|---|---|---|---|
| Z1/Z2/Z3/Z4 (zodiac labels) | 294 of 299 Lz loci | **91 of 299**, 0 with clock annotations | largest TEST ring is 5 labels; the ≥ 8 rule leaves no ring. Convention C has no design. Z4's TEST labels do not span more than one rank block |
| R1/R2 (Recipes) | 10,836 of 10,893 tokens (99.5 %) | **3,394 of 11,816 (28.7 %)**, mean word length 2.79 vs 5.21 | the EVA gallows set has no counterpart in what survives (opener "gallows" rate 0.056 vs 0.032 for all words, 1.2 SD). **0 star comments in the Recipes section**, so R2 has nothing to permute |
| L1 | 38,184 of 38,461 (99.3 %) | **9,426 of 40,175 (23.5 %)**; label words on both-register pages fall 1,008 → 297 | the frozen T2 merges are EVA merges and do not segment v101 at all |

The one GC2a number worth keeping is Z3's distinct/total = 78/91 = 0.857, which reproduces the ZL3b picture (0.878) and can only be biased downward by thinning.

**Nothing in this pass is transcription-replicated.** All results rest on ZL3b alone. Since everything failed, no transcription-dependent claim is being made — but a *positive* result could not have been replicated either, and fixing this is the highest-value infrastructure item for the next pass (§5).

---

## 3. What survived adversarial review

Every test was attacked under three lenses (null-correctness, confound, reimplementation). Fifteen verdicts. Below is every objection graded **material** or **fatal**, and what it did.

| # | test | lens | grade | objection | effect on the claim |
|---|---|---|---|---|---|
| 1 | Z1 | null-correctness | minor | Pooled Δ has non-zero H0 expectation (−0.0041); gate (ii) compares raw Δs | Effect-size ratio restated 3.98 % → **8.5 %**. Gate still fails by 3×. |
| 2 | Z1 | null-correctness | minor | "8/8 numeral controls" power is inflated: `cut_cyclic` builds 7 distinct rings of 10 | Power claim replaced with construction-free **detection floor Δ ≥ +0.042 (27 % of numeral median)**. Verdict unchanged. |
| 3 | Z1 | confound | minor | "With power to spare" holds at numeral effect size, not at the gate's own 25 % bar (power 0.42 there); dilution below ~50 % coverage undetectable | Headline narrowed; both figures now reported. |
| 4 | Z2/Z3 | null-correctness | **material** | Z3 TTR null draws **with replacement** from tiny cells | **z = +8.19 withdrawn** → +2.49 (p = 0.014) without replacement; sign reverses (z = −1.07) under the retag null. Not a stable finding. |
| 5 | Z2/Z3 | confound | minor | "Labels use a strict subset of the running-text inventory" | **Withdrawn** as pure rarefaction (expected 38.00 ± 1.08, 2.01 missed). |
| 6 | Z2 | null-correctness | minor | Null shuffles across rings although conventions B/C tie slots to rings; two-sided p uncentred; conv B control wraps 30 items over 44 slots | All three make the test *easier*; it failed anyway. Best cell restated as p = 0.026–0.033. |
| 7 | Z2 | null-correctness / confound | minor | "Power = 1.00" rests on a byte-identical straw control | Replaced with implantation floor (**~5 % of labels**) and degradation sweep (blind past ~80–85 % corruption). |
| 8 | **Z4** | **confound** | **FATAL** | "Thirds of the ring" remainder rule is unregistered; floor passes (0.0013), midpoint (0.024) and ceil (0.035) fail, while all three detect the numeral controls equally | **Gate outcome changed PASS → FAIL.** The finding is removed. |
| 9 | Z4 | confound | fatal (same) | "Thirds of the ring" implemented as thirds of the label list; angular third p = 0.0099, absolute dial third **negative** p = 0.597; k = 4 and k = 6 (more sensitive, 6/8 and 7/8) both flat | Confirms 8. |
| 10 | Z4 | null-correctness | material | True tail probability q = 0.001655 (CI 0.001529–0.001781) straddles the threshold; P(registered procedure declares pass) = **0.413**; the B = 200,000 "corroboration" reuses the gated seed | "Clears by 0.00007" withdrawn. |
| 11 | Z4 | reimplementation | material | Undisclosed seed 409 vs registered 408; family of six vs registered four | Disclosed. Does not rescue the finding (objection 8 kills it under either family). |
| 12 | Z4 | confound | material | Reported caveat "`ot` is depleted in the first third" is false (7/53, 10/47, 6/47; one-vs-rest p = 0.903) | Corrected; only the `y` depletion is real, and it is post-hoc selected. |
| 13 | **R1(b)** | **null-correctness** | **FATAL** | (b)/(c) null is a with-replacement cell bootstrap, not a permutation; measured type-I error **0.352 at nominal 0.05** | All (b)/(c) rejections void. Corrected null: **nothing rejects in any of six strata**. |
| 14 | **R1(b)** | **confound** | **FATAL** | Control-pool composition is unfrozen and decides the answer (TEST −3.51 → +0.75 SD; FIT −3.18 → +0.70 SD; halves anti-correlated) | **R1(b) reported as not identified.** Ornamental branch neither asserted nor refuted. |
| 15 | R1(b) | reimplementation | material | The −3.56 SD reversal comes entirely from 28 openers matched to buckets of 1–2 words attested at 0.985, with controls 1–3 chars shorter | Reversal withdrawn; forbidding shorter controls gives −0.03 SD, p = 1.0000. |
| 16 | R1(c) | null-correctness | material | Entropy control SD 7 × 10⁻⁵ → "−692.9 SD" | **Withdrawn** (null collapse). LEXICAL fail is unaffected — it is an absolute count. |
| 17 | R1(c) | null-correctness / reimplementation | minor | "`tchedy`, 4/134 = 4.35 %" conflates two denominators | Corrected to **4/134 = 2.99 %** (protocol denominator); 4.35 % is 4/92. Fails at both. |
| 18 | R2 | null-correctness | material | Page-stratified `tail` p = 1.0000 reported as a measurement, but the within-page null has exactly one realisation | Restated: the design cannot separate `tail` from page identity. Negative result unaffected (registered null is anti-conservative here). |
| 19 | **L1** | **reimplementation** | **material** | Under the pre-registered uncorrected MH the Culpeper control clears **4 of 25** and passes leg 1 — recorded in the test's own JSON | **Headline reversed**: the gate is calibrated; L1's FAIL is an informative negative, not "no evidence either way". |
| 20 | L1 | null-correctness | material | Continuity constant κ is unregistered and chosen with the strata in view; κ = 0.5 would pass | Disclosed. FAIL under 4 of 5 conventions including the protocol-literal and the harder reading. |
| 21 | L1 | null-correctness / confound | material | `daiin` is one lexical fact double-counted in both families; as a genuine suffix p = 0.13, as a genuine prefix it does not exist; type-level p = 0.607 | **`daiin` withdrawn from both families.** |
| 22 | L1 | reimplementation / null-correctness | material | `n`-final: uncorrected p = 0.121, placebo p = 0.025, dies on leave-one-out | **`n` withdrawn.** Word-final family now has zero durable findings. |
| 23 | L1 | confound | material | `c-` initial: 0 of 491 locus-initial text words carry it; sign flips to +1.095 under a symmetric position design; FIT p = 1.000 | **`c-` withdrawn.** |
| 24 | L1 | null-correctness / confound | material | `q-` and `qok-` are one phenomenon; control word-initial passers are 2 (not 0); leg-2 ratios are noise-floor / unit-vs-character comparisons | Restated as **one** fact (merged exact P = 2.6 × 10⁻¹⁸); ratios corrected to 0.816 / 0.755 / 0.842. |

**What the verifiers could not break.** Z1's estimator (bit-identical under a naive independent reimplementation; type-I 0.0050 at nominal 0.01; null result survives circular gaps, three poolings, bias correction, ring order taken from the ZL clock, dropped-locus repair, four similarity measures, length matching, per-ring max statistic with multiplicity correction, and duplicate removal — and the same 139 label strings reordered can reach Δ = +0.342, so the strings are perfectly capable of expressing a gradient). Z2/Z3's arithmetic (reproduced to 5–6 decimals; Z3's 258/294 reproduces exactly and is unconfoundable). Z4's MI, χ², permutation and p arithmetic (all clean; the design is sound, the one number it produced is not). R1(a) (survives every confound and is understated). R2's machinery (χ² exact, null correctly implemented, no survivors). L1's estimator algebra (sparse quadratic decomposition verified against a brute-force cell-by-cell recomputation to < 1 × 10⁻⁹; permutation null verified against a register-swap placebo; p-values re-derived exactly by hypergeometric convolution). All six input sha256 values verified independently by three separate lenses.

---

## 4. What this rules out

Each of these is a negative with a measured detection floor. The floor is the number that makes it a result rather than an absence.

**1. The nymph labels are not a written numeral series around the ring.** Detection floor: Δ ≥ +0.042, i.e. **27 % of the strength of a real written numeral system**, exactly computable because the permutation null is ordering-independent. All eight numeral systems tested (English, Latin, Italian, German, French, Roman, Greek Milesian, `d`+Roman) sit at 2.6×–5.9× that floor. The manuscript sits at **0.15×**. Any hypothesis in which neighbouring nymph labels share material the way `xxv`/`xxvi` or *vigintiquinque*/*vigintisex* do is now excluded at full numeral strength and down to about a quarter of it.
*Not excluded:* a numeral system whose neighbouring forms share no material at all (an arbitrary sign-per-number list); a numbering covering **under about half** the labels in a ring (detection 0.40 at 50 % coverage); or a numbering whose order is not the ring order the transcription records.

**2. The labels are not a per-sign numbering that restarts.** Z2 detects same-slot correspondence when as few as **10 of 147 labels (5 %)** carry it, under conventions A and C, keeping the manuscript's own vocabulary and length distribution. Nothing at or above that level exists. The one alignment gap the frozen conventions left open — a numbering that starts at a different nymph in each sign — was closed by a rotation-invariant test that returns z = +0.01. And Z3 forecloses the simplest version arithmetically: 258 of 294 strings distinct, within-sign distinct/total 0.93–1.00, when a restarting numeral list predicts ≈ 0.10.

**3. There is no rank-keyed morphology in the labels — no tens morpheme at the front, no ordinal suffix at the back.** On the four rank-block statistics the test detects **5–6 of 8** real numeral systems; the manuscript returns +0.0027 bits, −0.0281 bits, +0.195 and −3.657 (p = 0.92, 0.41, 0.97, 0.53). Across the finer ring partitions the same design detects **6/8 and 7/8** and the manuscript is flat there too (p = 0.46, 0.24). Taken with (1) and (2): **the strongest single conclusion of this pass is that the zodiac nymph labels are not a counting system in any form that a written numeral system would produce.** Three independent probes, each with a measured floor, agree.

**4. The Recipes section has no entry formula.** The commonest paragraph-opening word type is 2.99 % of openers against a 10 % bar, and openers are *more* lexically diverse than a matched control. There is no Voynich *Recipe* / *Item* / *Take*. This is an absolute-count result and no confound can move it.

**5. The drawn stars do not index the text.** No test of point count, `dotted` or `tail` against opening glyph, paragraph length or the 50 most frequent types survives Bonferroni on the held-out half — under a null that is *anti-conservative* for the page-clustered predictor, which makes non-survival the safe direction. What the machinery does detect at floor-level p is a real association: `tail` with page identity (Cramér V = 1.000). The instrument is not blind; the stars are not indexing.

**6. There is no ≥ 3-unit name/grammar split in word-final glyph units.** 2 of 25 against a calibrated control that clears 4 of 25 under the pre-registered estimator — and both manuscript passers dissolve under type-level deduplication and under the pre-registered estimator respectively, so the true count of durable word-final findings is **zero**. Whatever separates the label register from running text on these pages, it is not a system of endings.

**What became *harder to hold*, quantitatively:** the "labels are numerals" hypothesis, in every form the eight control systems instantiate, now requires either arbitrary unrelated symbols per number, or coverage under half a ring, or an ordering the manuscript does not record. The "paragraph opener is a lexical word" hypothesis requires that word to appear under 3 % of the time — which is not what a formula is.

**What did *not* become harder to hold:** the ornamental-initial reading. It is untested, not supported. §2.5 explains why.

---

## 5. Open questions and the next probe

**Caveats carried forward, in priority order.**

1. **Nothing here is transcription-replicated, and with the current shared library nothing can be.** `clean_tokens`'s `[a-z]+` filter destroys 70–77 % of GC2a and all of its zodiac ring structure. A positive result in this pass would have been unreplicable for the same reason. **This is the single highest-value fix for the next pass: a v101-aware tokeniser plus v101-derived byte-pair merges in `meaning_lib`, verified by round-tripping the ZL3b results through both alphabets.** Until it exists, "replication on an independent transcription" is not a real gate condition in this repository.
2. **R1(b)'s design has to be rebuilt before the ornament question can be asked again.** Two defects, both fixable and both frozen into the current protocol: (i) the resampling null must be a conditional within-cell label permutation (CMH), not a with-replacement cell bootstrap — the current one has type-I error 0.35 at nominal 0.05; (ii) the control pool must be frozen in the pre-registration (which pages, tokens vs types, and what happens when no length-matched control exists), because that unfrozen choice moves the answer from p = 0.0004 to p = 0.51. The coverage limit is also real and structural: for openers of length 9–11 the section contains **no** gallows-matched control at all, so the design can never speak to the longest quarter of openers. A redesign should match on gallows and length *within* a paragraph-position-symmetric frame (first word of an L locus vs first word of a P/C/R locus), which the confound lens showed is the only comparison that removes the locus-position artefact.
3. **The same matched-resample pattern should be audited wherever else it is reused.** L1's within-page matched permutation was checked and is clean (verified against a register-swap placebo and against exact hypergeometric convolution). Any future test that draws a matched control with replacement from small strata inherits R1(b)'s defect.
4. **Two unregistered analyst degrees of freedom decided a gate outcome in this pass** (Z4's remainder rule; L1's continuity constant), and a third nearly did (Z4's Bonferroni family size). Future pre-registrations must fix: partition remainder rules, estimator corrections, control-pool scope, permutation sidedness, and the exact family over which multiplicity is corrected. A gate whose outcome turns on a knob the protocol does not name is not a frozen gate.
5. **The `L` locus code is editorial.** Every L1 result and every label-register claim inherits whatever judgement went into Zandbergen–Landini's assignment of `L`. This is not testable from the transcription alone; it needs the images.
6. **Z1's gate design has a self-inconsistency worth fixing.** The detection floor (27 % of the numeral median) sits marginally *above* gate condition (ii)'s 25 % bar, so an effect exactly at the bar could not clear condition (i). Power at the gate's own threshold is 0.42. Z2 uses the same 25 % construction.

**What the next pass should run, given these powers.**

- **Do not re-run Z1/Z2/Z4 on the zodiac labels.** Three independent, well-powered probes agree that no numeral structure of the kind written numeral systems produce is there. Spending another pass on this is spending it on a measured null. The only version still open is *arbitrary symbols per number*, which by construction leaves no sequence-similarity signature — meaning it cannot be tested by any similarity statistic and needs a different kind of evidence entirely (co-occurrence with drawn quantities, or an external ordering).
- **Run the q-initial depletion as a pre-registered gate, not a side-observation.** It is the only effect in this pass that is large, exactly computable, and present in both halves of a held-out split (merged exact P = 2.6 × 10⁻¹⁸ on TEST, 2.3 × 10⁻¹⁵ on FIT), and it survives type-level deduplication, position control, page dropping and leave-one-page-out. It is currently unclaimable because it sits in a family the protocol never registered. A pre-registration that states it as a hypothesis — *EVA `q` marks a class of word that does not appear as a label* — with its own gate, its own positive control (an English/Latin function-word class that is likewise absent from headings), and a genuine replication on a v101-aware parse, would convert folklore into a result. Note the honest ceiling first: this is a *prefix* result and does not by itself license a name/grammar split, and at matched measurement level the Culpeper control detects more units than the manuscript does.
- **Test the paragraph-opener question a different way.** The ornament-vs-word question is worth answering and R1(b) cannot answer it. A cleaner design: compare the *residue* distribution of paragraph openers against the distribution of the same words at line-initial positions inside paragraphs, matched on locus position rather than on token frequency, with a conditional null. R1(a)'s 31.8 SD (length-matched) says the phenomenon is real and enormous; only the interpretation is unresolved.
- **Do not spend a pass on R2.** The design cannot separate the two star attributes that vary within page (`dotted`, point count) from a null at n = 130, and `tail` is not a star property at all. If the stars are ever to be tested, it needs per-star annotation from the images rather than the transcriber's per-page boilerplate.

---

## 6. Reproduction

**Environment.** Python 3, stdlib only (no numpy, no scipy). Git Bash on Windows; heredocs unusable. Every run: `export PYTHONIOENCODING=utf-8`.

```bash
cd "R:/Coding/LinearA/tmp/voynich_repo/experiments/meaning-probes"
export PYTHONIOENCODING=utf-8
python smoke.py          # parser sanity check
python t_z1.py           # -> results/z1.json,    results/z1.stdout.txt
python t_z2z3.py         # -> results/z2z3.json,  results/z2z3.stdout.txt
python t_z4.py           # -> results/z4.json,    results/z4.stdout.txt
python t_r1r2.py         # -> results/r1r2.json,  results/r1r2.stdout.txt
python t_l1.py           # -> results/l1.json,    results/l1.stdout.txt
```

Verifier scripts are `v_<key>_<lens>_*.py` in the same directory, with outputs under `results/` (prefixed `v_`). They are re-runnable the same way.

**Protocol deviations found by the completeness audit** (`results/completeness_critic.md`), beyond the errata already recorded in §2.4, §2.5 and §2.7:

- `PROTOCOL.md` §Data says *every* test is run at glyph-unit level with a raw-EVA robustness arm. **R1 was run at EVA-character level only** — `t_r1r2.py` uses glyph units solely for R2's `first_glyph_unit` outcome, and the `runs` block varies corpus and `comma_split` but not segmentation level. Z1, Z2/Z3, Z4 and L1 all carry both levels. R1(a)'s gallows set is defined on characters and would not change; R1(b)/(c)'s residue and matching definitions would. This does not affect any verdict in this report — R1(c) fails on an absolute count and R1(b) is withdrawn as unidentified — but the missing arm should be run before R1 is redesigned.
- `results/z4.json` reports `sorted[4]` of 8 as the numeral-control "median" (`MI_P2_F1`: 0.1134 against a true median of 0.0964). Conservative in direction, mislabelled in the file. Z4 is FAIL regardless.
- `mc_stability_diagnostic.seed_sensitivity_B10000` in `results/z4.json` counts seed 409 among its ten "independent" draws; 409 is the gated stream itself, so the figure is 6 of 10 with one draw not independent.
- Housekeeping: several verifier runs left no artefact under `results/` (`v_z1_null-correctness_1/2/3`, `v_z2z3_confound_1`, `v_z2z3_null-correctness_*`, `v_z2z3_reimplementation_b`, `v_r1r2_null-correctness_*`, `v_r1r2_reimplementation_d`), and `v_z1_reimpl_a.json` / `v_z1_reimpl_b.json` sit in the pass root rather than in `results/`. The scripts are re-runnable.

**Seeds.** RNG seed **408** everywhere, 10,000 permutation draws, unless a line below says otherwise.

| deviation | where | value |
|---|---|---|
| ring-third permutation family | `t_z4.py:342` (`seed + 1`) | **409** — undeclared departure from the registered 408; at 408 the same statistic gives p = 0.00090 |
| Z4 high-precision diagnostic | `t_z4.py` | seed 409, B = 200,000 — reuses the gated stream and does not corroborate it |
| Z3 TTR resample | `t_z2z3.py` | seed 408, 1,000 draws |
| verifier independence seeds | various `v_*` | 409, 777, 10408, 20408, 30408, 40408, 20260907, sweeps 400–439 |

**Input sha256.**

| file | sha256 |
|---|---|
| `data/corpora/ZL3b-n.txt` | `bf5b6d4ac1e3a51b1847a9c388318d609020441ccd56984c901c32b09beccafc` |
| `data/corpora/GC2a-n.txt` | `b09570cb6c993bc2d87134d115e60a978650a8a6495483ddbb1f6005a586096f` |
| `tmp/voynich_lab/pg49513.txt` (Culpeper) | `d9bacb3247d798fcd2a8ce3b7c76222407fc0ac1c8d4242e9e8163508c10e968` |
| `tmp/voynich_lab/bibles/Latin.xml` (Vulgate) | `5bba9f75c06858a28ebe7b2fcc19cc32b3fbf587d6bc237ceac6fe7addd3df31` |

**Code sha256 at the time of the run.**

| file | sha256 |
|---|---|
| `PROTOCOL.md` | `26847ad7f72579958ac48ee4d284aa275df0a5a6a0143b148b39ae9c759b83dd` |
| `meaning_lib.py` | `aa1ee5a340923cf7bd3f5aa1d433d24c10b2db50da1e7b2da9256cd98ef42fb1` |
| `t_z1.py` | `8dde40b058511d60e82129afb9adcbda8c1317fc5c852b6b7716df97650f8711` |
| `t_z2z3.py` | `bdb9a05582233201c88921cc3204c83c567186e7a5dcd74155a558ed872f2b6c` |
| `t_z4.py` | `3e55dee956ae3485ae969fae8c4ceb207f2776e44ef11fd93ea7b91310fc9991` |
| `t_r1r2.py` | `2929fa7da5808539d39356fa6d34d10287ade54e8d47022294bb6fc1e8342445` |
| `t_l1.py` | `86cd9b504ee62cbff9c3164ebfe578422729e33c808a633e8c04c492987b2576` |

The `t_z1.py` self-hash recorded inside `results/z1.json` still matches the file on disk, so that script was not edited after its JSON was written. No `t_*.py` script or `results/<key>.json` was modified during adversarial review or while writing this report; the two errata (§2.4 `z4.json` `gate.outcome`, §2.7 `l1.json` `estimator` and page count) are recorded here rather than patched into the machine-readable output.

**Frozen glyph units.** The 20 byte-pair merges from T2 (protocol `318a679`, freq mode, corpus `Voynich_S`), applied in order: `ch dy ai ok ol ee sh in che aiin ot ar al qok or she eey ain daiin chedy`. Every test also run at raw EVA-character level.

**Provenance.** Tests, adversarial review and this report were produced by Claude Code (Anthropic), model `claude-opus-5`, under the frozen pre-registration above. Gates were not adjusted after any statistic was seen; where the protocol was ambiguous, the reading taken is stated inline and, in each case, is the reading that makes the test harder to pass.
## Data availability

The corpora used in this pass are served, with identical sha256 hashes, by the Artheon Museum Lab open dataset for Beinecke MS 408: https://lab.artheonmuseum.org/voynich/ (machine catalogue https://lab.artheonmuseum.org/voynich/catalogue.json; agent entry point https://lab.artheonmuseum.org/voynich/README.md). ZL3b-n.txt = bf5b6d4a…beccafc and GC2a-n.txt = b09570cb…586096f there and in this repository's data/corpora. The dataset also serves the 213 full-resolution page scans (Beinecke IIIF), which the image-based follow-ups proposed above require.
