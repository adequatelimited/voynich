# Contribution scoring, v0.1

**5. Scoring v0.1: outcome credit, not activity credit**

Implement this as a provisional normative rubric in `scoring/rubric-v0.1.yaml`, with readable guidance in `SCORING.md`. Its numbers require calibration, not a claim of scientific measurement. Publish and implement the complete AI methodology in `GRADING.md` and global rules in `RULES.md`; Rule R1 is No Score Gaming. All production grades and regrades come from that AI pipeline with deterministic allocation arithmetic. Freeze v1.0 after the actual-model pilot in section 17. Any references to reviewers/assessments in contribution anchors include the official AI evaluator; requirements for independent execution or external scientific evidence are separate and cannot be satisfied by model role-play.

The scoring unit is an **independently useful research outcome**. It has a stable family ID, a before/after statement, a mission-linked question, an acceptance test, evidence, and a dependency explanation. Files, citations, glyphs, paragraphs, tokens, CPU hours, commits, model calls, and PR counts are not scoring units.

Apply a marginal-value test: does the claimed unit provide distinct useful information or a capability beyond the other claimed units, with its own acceptance test? Dependencies are allowed: an experiment can depend on a parser while producing a separately useful finding. A corpus correction, reusable parser and falsifying experiment can be three outcomes. A parser's README, tests, report and packaging normally belong to its one outcome. Reviewers must identify legitimate omitted outcomes as well as reject artificial fragmentation, and explain the decomposition publicly.

Each family has a public scope record: question/capability, decision it informs, input population/corpus region, protocol and selection rules, acceptance evidence, completion boundary, predecessors/siblings/aliases and excluded overlap. Candidate-direction cards may mark detailed inputs/protocol/selection rules as undeveloped; their tier-2 acceptance evidence is the inspected usefulness, distinctness, rationale and plausible next step of the suggestion. A systematic import defect affecting 300 records is one correction outcome, not 300. Variations within one parameter/language search are one analysis program unless they establish a distinct material result. Folio partitions, source-list subdivisions, file formats, release numbers and branches are not automatic family boundaries. A cross-branch finding supplying the same information receives one award. A proposed task scope supplies expectations; it does not reserve ownership or guarantee points. Ambiguous boundaries require a published analogy and reasoned scope decision that can be appealed.

Before assigning a positive tier, all gates must pass:

1. A clear connection to an existing research question, a clearly scoped proposed new question, or a necessary shared research capability.
2. Traceable sources/inputs and an acceptable rights/provenance record.
3. Inspectable evidence appropriate to the contribution type; executed claims require commands, inputs, and actual outputs. Formal proofs require independently checkable arguments, and expert observations require inspectable loci, criteria and uncertainty; neither must invent an inappropriate executable experiment.
4. Explicit scope, assumptions, uncertainty, contrary evidence, and limitations.
5. Required human attribution and AI-use disclosure.
6. Incremental value beyond existing outcomes, with related work and family overlap examined.
7. No fabricated evidence, concealed material selection, or unsupported claim presented as established fact.

Missing gates mean `needs_revision`, `unscored`, or rejection with reasons. A useful zero-point change can still merge. Accessibility or platform improvements qualify when they demonstrably enable research participation or reliability; generic cosmetic activity does not.

| Cumulative tier for an outcome family | Points | Evidence anchor |
|---|---:|---|
| Acknowledged activity | 0 | Duplicate, routine presentation change, unsupported speculation, or insufficient evidence for positive credit |
| Bounded verified improvement | 2 | A checked material correction/source contribution, or a distinct useful candidate work direction with a clear question/approach, research rationale, bounded prior-work check and plausible first investigative step; a complete protocol or executed result is not required |
| Completed reusable contribution | 5 | A coherent source synthesis, validated dataset/annotation batch, usable protocol/tool, or informative pilot that another contributor can inspect/use |
| Reproducible research result | 10 | A controlled discriminating experiment, substantive independent replication, or material corpus/method improvement with appropriate baselines, checks, and independent inspection/execution |
| Independently validated major advance | 20 | A substantial new constraint on a defined hypothesis class or broad demonstrated research capability, with independent validation and a nonconflicted external domain assessment |

Use the highest fully satisfied tier, not an average of subjective subratings. Record gate evidence and rubric anchors explicitly. No bonuses for a famous name, popular language hypothesis, AI model, dramatic prose, GitHub reactions, or a positive conclusion. An informative negative result can earn the same tier as an equally rigorous positive one.

Provide type-specific anchors in the scoring handbook:

| Type | Typical 2-point outcome | Typical 5-point outcome | Route to 10 or 20 |
|---|---|---|---|
| Sources/history | Verified correction that changes a cited fact or resolves a material provenance gap | Original comparative synthesis with checked claims and a reusable evidence table | A validated finding that materially constrains a research claim, with qualified assessment |
| Corpus/annotations | One materially useful correction set with verified loci | Coherent, independently checked annotation/corpus batch and uncertainty report | Demonstrated impact on analyses across corpora/sections, with controls and replication |
| Research directions | Distinct useful suggestion with rationale, prior-work check and plausible first step | Developed independently reviewed usable protocol, or completed validated pilot | Executed discriminating study; the direction/protocol credit is part of its family total |
| Tools/methods | Bounded fix that repairs a demonstrated research failure | Reusable tested tool with worked manuscript example | Measured validity/reliability improvement and independent use; scale claims require evidence |
| Experiments | Small verified diagnostic observation | Informative controlled pilot | Reproducible discrimination or falsification, then broad independent validation |
| Replication/review | Verified material defect report | Substantive reusable audit or partial replication with informative limits | Independent reproduction/failure analysis that changes confidence or research decisions |

These are evidence anchors, not automatic points per row, source, or correction. Reviewers consolidate a coherent batch into its natural outcome scope. Bare link dumps, vague or materially repetitive suggestions, repeated random seeds, and ordinary approval comments do not become credit streams. A specific useful unexecuted direction can qualify under section 5b.

**5a. Contribution coverage atlas**

Use this atlas in the contributor wizard, rubric examples, reviewer training and coverage tests. The tiers remain 0/2/5/10/20, with the universal evidence gates and family rules; no row grants points simply for producing a named artifact. Earlier type examples are illustrative. This atlas makes their coverage explicit and includes valuable work that earns public service acknowledgment without competitive points.

Research-relevant artifacts are explicitly eligible contributions: documents/PDFs, scans and images, annotations, datasets, dictionaries, notebooks, source code, tools, research harnesses, workflow configurations, benchmarks and reproducibility bundles. They can earn credit for making useful material available, inspectable or reusable by the project without proposing a translation or reporting a new manuscript finding. The material need not be globally new; its addition must provide verified marginal value to the shared research. Require a description of that value, a linked question/capability, provenance/rights, usable documentation and type-appropriate validation. Score the useful outcome, not file count, upload size or the act of uploading. An independently useful artifact can be a separate outcome; files merely supporting an already credited outcome are included in that outcome.

| Contribution route | Scoring boundary and evidence | Canonical category for a qualifying increment |
|---|---|---|
| Literature discovery and source verification | 2 for a material checked correction or provenance resolution; 5 for a new useful checked synthesis. A link, copied abstract or already-cataloged fact alone earns 0. | `sources_history` |
| Source acquisition, rights resolution, digitization and preservation | 2 for demonstrably removing a material access/rights obstacle; 5 for a usable provenance-preserving resource; 10/20 require independently demonstrated broader enablement. Purchasing access or claiming ownership earns 0. | `corpus_annotations` |
| Transcription, glyph/region annotations, image processing and alignment | 2 for a coherent material correction set; 5 for a checked batch with coverage/uncertainty; 10/20 require demonstrated analytical impact. No per-glyph/page/crop payment. | `corpus_annotations` |
| Comparative corpora, dictionaries and historical-language resources | Apply corpus/source anchors to selection, dating, normalization, rights and demonstrated usefulness. A checked translation of relevant scholarship can qualify; duplicative unchecked machine translation earns 0. | `corpus_annotations` |
| Expert paleographic, codicological, linguistic, historical or material assessment | 2 for a documented material observation; 5 for reusable checked analysis; 10/20 for independently validated constraints. Credentials alone earn 0; evidence may be loci and an auditable argument instead of code. | `sources_history` |
| Evidence synthesis, conflicting-claim reconciliation and cross-branch integration | 5 for a new reusable checked evidence structure resolving a defined uncertainty; 10/20 for validated analytical implications. Administrative graph rearrangement or restatement earns 0. | `publication_synthesis` |
| Candidate work directions, developed proposals and preregistrations | 2 for a distinct useful suggestion with rationale, prior-work check and plausible first step, without requiring a full protocol or execution. A developed independently reviewed usable protocol can reach 5. Registration/branch creation alone earns 0; later work upgrades the same family. | `proposals` |
| Experiments, diagnostics, controls, benchmarks and sensitivity studies | Apply the ladder to information gained and justified scope, including informative positive, negative, inconclusive or failed results. Repeated seeds/model variants alone earn no separate award. | `experiments` |
| Formal analysis and theory | 2 for a bounded checked observation, 5 for a reusable rigorous derivation, 10 for a substantive independently checked result, 20 for a validated major constraint. Include proofs, identifiability, impossibility, equivalence and complexity results with assumptions and counterexample checks. | `tools_methods` |
| Candidate decipherments and translations | Score explicit methods, reproducible mappings and validated constraints under the ordinary ladder. A narrative, isolated match or unsupported solution announcement earns 0 as a scientific result. Endorsement remains separate. | `experiments` |
| Reusable software, tools, harnesses, workflows and research instruments | 2 for a demonstrated material repair, 5 for a usable tested capability, 10/20 for measured independent benefit. Include analysis notebooks, code libraries, agent/research harnesses, workflow configurations and reproducibility bundles when their research utility is demonstrated. A harness needs a runnable worked example with actual inputs/outputs, configuration, controls and resource limits. Ordinary documentation/tests/packaging are included; lines of code and generic scaffold uploads earn 0 by themselves. | `tools_methods` |
| Replication, falsification, adversarial analysis and substantive review | Credit new assurance/information at the justified tier, including informative failure to reproduce. No points per approval, disagreement or defect allegation; a routine rerun is validation/service unless it adds a distinct finding. | `replications_audits` |
| Infrastructure, reliability, security and archival integrity | Use capability anchors for verified removal of a research barrier or material risk. Routine hosting/deploy clicks/compute donations earn 0. Sensitive evidence uses restricted review plus a redacted public artifact after remediation; a secret assertion cannot justify an unverifiable public score. | `research_enablement` |
| Accessibility, localization, onboarding and reusable training | 2 for removing a demonstrated participation blocker; 5 for independently usable checked capability/curriculum; 10/20 require substantial measured enablement. Clicks, attendance, recruits and hours earn 0. | `research_enablement` |
| Mentorship, coordination, moderation and community operations | Routine work receives named, consent-aware noncompetitive role/service acknowledgment. A distinct reusable artifact can qualify under another route; no referral or moderation-volume points. | None for routine service |
| Publication, scientific communication and research releases | 5 for an original checked synthesis or independently useful publication artifact; 10/20 only for new validated value. Reusing already credited findings does not re-award their research value. Routine formatting, manuscript submission or promotion earns 0. | `publication_synthesis` |
| Funding, hardware, commercial services and advocacy | Acknowledge support appropriately; money, equipment, paid services, publicity and influence cannot buy research points, authorship or review authority. Any separately authored research artifact follows the ordinary rules. | None for support itself |
| Previously unclassified work | Publish an interpretation using the nearest justified anchors, evidence and boundary examples through governance. Accept relevant material unscored while unresolved; neither a secret bonus nor permanent exclusion is allowed merely because a route was omitted. A substantive rule change follows the prospective policy process. | Explicitly assigned before credit |

Assess usefulness as a marginal contribution to the shared research, not a requirement that every curated fact be globally new. Preserve scholarly attribution to original researchers; do not credit importing a source as discovering all its findings. Publish a consent-aware service/contribution record alongside the competitive leaderboard so necessary routine stewardship is visible without turning it into a points market. Score eligibility never determines a person's publication role by itself.

**5b. Candidate work directions and recognition of useful suggestions**

A candidate work direction is a suggestion about how the community could approach the challenge: a new angle, question, connection, comparison, method to try, or material refinement of an existing investigation. Such suggestions are explicitly scoreable before anyone performs the proposed work. They need not contain a complete experimental protocol or promise a positive result.

Create `research/directions/<id>.yaml` and a matching contribution manifest. A tier-2 direction identifies: the specific approach/question; why it could advance a research decision; what materially distinguishes it from existing directions; a bounded check of the repository and relevant prior work; a plausible first investigative step; known limitations; and proposer/source attribution plus AI disclosure. It can link to an existing branch or introduce a scoped new question. Reviewers assess prospective usefulness and distinctness at the time of acceptance, not whether the hypothesis eventually proves correct.

Novel wording is insufficient. Distinguish an original-to-project suggestion from an adaptation of cited prior work, and disclose the scope of the originality check rather than claiming exhaustive global novelty. A useful new application of an existing method can qualify. “Try language X” or “use another AI model” without a material rationale/approach is normally 0; repeating one idea across pages, accounts or branches earns no extra credit. Preserve proposer and relevant co-discovery attribution when consolidating duplicates.

Award 2 for an accepted qualifying direction. If someone later supplies an independently reviewed usable protocol meeting tier 5, award the additional 3 to the responsible contributors. A qualifying study at tier 10 adds another 5. The initial suggester retains their valid 2 even if another team develops the idea or the investigation yields an informative negative result. They receive no ownership, veto, or automatic share of later work. Correct an original award only when its own evidence/novelty/representation failed the applicable standard.

Show accepted directions in the research map and an open-directions list with their proposer, rationale, score decision, status and next step. Acceptance signals a useful avenue to investigate, not an endorsed decipherment claim. Include calibration examples where a well-motivated direction earns 2 without a protocol, a generic suggestion earns 0, a materially distinct refinement earns justified credit, and paraphrased/partitioned duplicates earn 0 additional points.

**6. Incremental credit, attribution, and anti-gaming**

Settle materially overlapping accepted milestones in a stable family order: research-PR GitHub merge time, with dependency order breaking equal timestamps, then stable repository/PR IDs. Never use award posting, webhook arrival, author-supplied times or reviewer preference. Before awarding a later extension, settle the evidence tier of earlier already-merged overlapping claims. A vague prior-idea assertion, unmerged proposal or broad registration cannot reserve credit or block settlement. The queue must show the exact predecessor causing a hold and a review owner; unrelated families continue.

Settle at most one cumulative milestone per family per accepted research PR, using its highest justified tier and allocating the increment among responsible contributors. Intermediate artifacts in that PR provide evidence, not separate dated milestones. A single PR containing proposal, pilot and completed study for one family therefore settles once at the justified final tier; it does not create ambiguous same-time ordering or extra credit.

Maintain separate `current_evidence_tier`, `credit_high_water_tier`, beneficiary allocations and withheld allocations. The high-water tier records the portion of the ladder already occupied by accepted seed value or settled outcomes, including waived/reserved credit. It is an allocation baseline, not scientific confidence, and does not fall automatically after a credit correction. For ordinary progression:

```text
new_credit = max(0, approved_cumulative_tier - credit_high_water_tier)
credit_high_water_tier = max(credit_high_water_tier, approved_cumulative_tier)
submission_credit = sum(new_credit across independent approved outcome families)
person_credit_units = new_credit * attribution_share_basis_points
1 point = 10,000 credit units
```

An outcome family's ordinary cumulative credit cannot exceed 20. Record every milestone and its contributors rather than assigning all later credit to the originator. A proposal at 2, pilot at 5 and experiment at 10 earn increments of 2, 3 and 5. A genuinely independent reusable tool may be a separate family. A large submission with several independent outcomes has no arbitrary total cap; it needs evidence for each. If A's tier-5 work merges before B's tier-10 extension but B's decision arrives first, hold B's dependent award until A's tier settles: A receives 5 and B 5 regardless of adjudication order.

Register designated seed artifacts with immutable family IDs, assessed evidence-tier baselines and zero competitive allocations. A seed tool already at tier 10 occupies that baseline; an extension to 20 earns at most 10. Zero applies to designated seed work, not founder identities forever. Founders' later research can qualify under the same conflict rules. An unassessed seed must have its baseline resolved before dependent credit is settled; a zero point total is not evidence that the baseline is zero.

A saturated family can have a successor only for a new material uncertainty or newly demonstrated capability with a distinct acceptance test, explicit predecessor/overlap links and exclusion of previously credited evidence. A new release, account, rubric, output format or passage of time is insufficient. Substantive new replication in an untested domain can qualify; another unchanged rerun cannot. This rule allows useful research after tier 20 without letting aliases refill a ladder.

Scientific replication is a separate assurance outcome only when it contributes new independent implementation, data, controls, or analysis with a defined information gain. Merely rerunning the author's command is normally validation of the original outcome. The same replication evidence cannot simultaneously earn full new-result credit, full replication credit, and a duplicated original-family upgrade. Record which increment it supports. For example, an original study earns 10; independent replicators establish its family at tier 20 and receive the additional 10, with no second award for that same assurance outcome. A separate replication family requires a distinct information increment and an explicit record of which overlapping original-family credit is excluded.

Corrections use explicit correction events, not the ordinary new-credit formula or automatic redistribution. They preserve novelty/high-water history and do not reopen a reward for reverted/reintroduced work. Reassess dependent evidence and allocations when affected; do not assume they survive an invalid predecessor. Correct only the justified allocations and preserve their original earning dates. A factual attribution correction can reassign credit only after a separate reasoned finding identifies who actually performed that work. A removed allocation is neither automatically someone else's property nor an available bonus pool. Restoring an incorrectly revoked valid award restores its original allocation/date. Enforce nonnegative net balances and conservation across paid, withheld, withdrawn and seed-occupied portions of the ladder.

Required correction example: A received 10 and B's validation raised the family to 20, earning B 10. Reducing A's award to 5 ordinarily gives A 5 and B 10; the vacated 5 stays unallocated and the credit high-water remains 20. B gets no automatic extra 5 merely for being later. Additional assignment to B requires evidence that B actually supplied that improvement. If B's validation is undermined, reassess B too. A genuinely new repair/constraint can qualify under the successor rule when it supplies distinct information; fixing one's own original acceptance failure is not a fresh outcome. Score correction alone never changes the earning period.

Use integer basis points for joint attribution, totaling exactly 10,000 per increment. Confirm leaderboard beneficiaries through the GitHub-authenticated responsibility acknowledgment in section 9; do not infer ownership/shares from commit or PR authors alone. Historical source authors receive ordinary scholarly attribution and do not need GitHub accounts or leaderboard consent. Missing/disputed acknowledgments hold the affected credit units outside rankings rather than giving them to the submitter. Evidence-tier settlement can proceed, with a published reason and provisional share map summing to 10,000; any genuinely disputed residual is assigned to a non-ranking reservation ID. Only the demonstrably uncontested share may publish. Sound research and genuine later extensions need not wait for a missing person's consent. A later reviewed release binds real beneficiaries and retains the original earning date.

Changed beneficiary/share assignments need authenticated acknowledgment for newly published credit; justified reductions/revocations do not require recipient permission. Appeals resolve credit theft or disagreement, and absent beneficiaries never silently forfeit to the submitter after a timeout. For simultaneous independent discovery, inspect verifiable provenance predating exposure to the competing work, allow conserved joint attribution when justified, and distinguish genuinely new assurance from duplicate evidence. A private assertion of priority supplies no veto. Credit human responsibility; AI systems are disclosed tools, not personal leaderboard entries. Teams aggregate existing allocations without duplication.

Require semantic duplicate review against the outcome registry, normalized input/output hashes where useful, and explicit `extends`, `duplicates`, `depends_on`, and `independent_replication_of` links. Automated similarity flags assist review and do not decide scientific novelty. No rule can completely prevent gaming; publish residual risks and resolve them through reasoned adjudication.

Family alias consolidation is an explicit reviewed registry/credit migration. Preserve every original ID and artifact, select the canonical scope, map overlapping milestones, and correct duplicated allocations with reasons. Identical-family high-water baselines are not added together; evaluate the justified canonical ladder and retain its consumed history. Contributions whose distinct scopes survive remain separate. Neither retrospective alias discovery nor a newly alleged older milestone may silently redistribute published credit; use the correction/priority process with authenticated evidence. Candidate scope, seed and alias records cannot alter official baselines until their trusted decision is accepted.

Adversarial cases required in the rulebook and executable fixtures:

| Case | Required result |
|---|---|
| One coherent corpus cleanup split into 20 PRs | One family with the same total credit as the consolidated outcome |
| Proposal 2, completed study 10 | 2 then 8 additional points; 10 total |
| A 10-point tool extended to 20 by another team | Original allocation remains; extension earns 10, allocated to its contributors |
| Twenty citations copied without verification | No positive credit merely for volume |
| Convincing generated translation with no reproducible mapping | No scientific-result credit |
| Well-controlled result contradicting an operator's hypothesis | Eligible under the same anchors; conflicted operator recuses |
| Two names claiming the same evidence as independent work | Consolidate or investigate; no duplicate total |
| Independent replication exposes a real prior error | Score the new assurance outcome; correct the earlier award only if its original evidence/claims failed the standard |
| Hypothesis later falsified despite sound original work | Preserve earned methodological credit; update scientific state |
| Reviewer submits an ordinary approval as a new contribution | No points; a separate substantive audit artifact can qualify |
| Delete/re-add, account rename, PR replay, or restored award | No fresh credit or period reset |
| Operator seed materials | Public provenance, zero competitive points |

Use a default triage limit of three new untriaged scored submissions per account to protect reviewer capacity; queue extras without rejecting legitimate work. This is a workload control, not proof of unique personhood. Handle suspected coordinated accounts through confidential investigation, published redacted decisions, and appeal. Do not infer misconduct solely from a shared model, IP address, institutional affiliation, or unpopular hypothesis.

**6a. Scoring abuse controls and retained tradeoffs**

| Attack or distortion | Required prevention/detection and response |
|---|---|
| Proposal/source/annotation farming | Require material marginal usefulness, prior-work check, scope and type-appropriate acceptance evidence. For candidate directions, a plausible first step and reason the approach could change a research decision suffice; a full experimental test is not mandatory at tier 2. Consolidate variations of one search/import/curation program across PRs. Creating a branch/registration earns no automatic credit. Distinct genuinely useful suggestions/outcomes may still accumulate. |
| Family aliasing and saturated-cap evasion | Resolve aliases before scoring; require the scope/successor record and semantic review across branches, periods and rubric versions. Hash similarity is evidence, not an automatic novelty decision. |
| Seed laundering and founder favoritism | Freeze assessed seed baselines with zero allocations. Neither another account nor a founder relabeling seed work can reclaim it; later founder work uses ordinary independent review. |
| Reviewer rings, coercion and gatekeeping | Routine grading uses the published AI pipeline and independent stage contexts; contributor-provided model personas or approvals cannot supply trusted review authority. For human scientific evidence, factual appeals and governance, exclude material direct collaboration, supervisory/financial interests and promised reciprocal findings; record recusals and use an uninvolved qualified person for disputed facts. Audit operator access, evidence selection, queue concentration and collusion patterns without inferring guilt from patterns alone. No participant or operator may reserve branches or delay competitors to acquire credit. |
| Account aliases and fabricated independence | Stable GitHub IDs identify accounts, not unique people. Voluntary linked identities and evidence-based alias adjudication share credit history, newcomer age and intake limits; retain historical IDs. Multiple accounts do not supply independent validation or fresh entitlements. Avoid invasive identity collection and unsupported identity inferences. |
| Credit theft, absent collaborators and coerced shares | Separate scholarly attribution from score beneficiaries; retain provenance and responsibility acknowledgments, withhold disputed allocations, and provide independent appeal. No default transfer to a submitter or automatic windfall on correction. |
| Self-created defects and repair farming | Judge net change against the last valid capability, not a deliberately weakened intermediate version. A regression, withheld required evidence, benchmark weakening or ordinary completion of one's prior obligations earns no new credit. Encourage honest self-correction; misconduct requires separate evidence and process. |
| Rubric shopping and migration laundering | Derive a new family's rubric from the authoritative policy effective at its first accepted artifact, not its requested version. Existing families stay pinned unless explicitly migrated. A rename or rule change cannot reset consumed tiers, re-award old evidence or move credit into a new period. |
| Cherry-picked runs, restricted evidence and false AI disclosures | Require all material variants/failures within the declared experiment/search scope, justified exclusions, inspectable provenance and suitable independent checks. Never claim to verify every private experiment or use an AI detector as proof of dishonesty. Unknown versions stay unknown; demonstrated concealment triggers correction/investigation. Restricted evidence supports only the verifiable scope or remains unscored. |
| Merge-time and queue manipulation | Publish receipt/readiness/merge/posting times, queue reasons and holds. Do not let operators schedule merges to favor standings. Server timestamps prevent backdating, not strategic withholding or all reviewer delay; describe period scores as accepted contributions, not the date work was performed. |
| Appeals, moderation and audit-volume farming | Routine appeals, successful reversals, ordinary reviews and ledger clerical repairs earn no points by themselves. A distinct substantive audit with useful findings can qualify once. Publish service acknowledgments separately. |

Maintain `scoring/threat-model.md` with each attack, assumptions, control, detecting evidence, authorized responder, appeal path and regression fixture. No list is exhaustive. Subjective value, hidden collaboration, private experimentation, resource advantages and timing remain partially observable. Aggregate credit can legitimately rank many modest useful contributions above one rare breakthrough; expose category totals, significant-result narratives and that limitation instead of secretly adjusting totals. Review emerging abuse and type-coverage gaps regularly; change future rules through the published process.

Required numerical/property fixtures beyond the earlier examples:

| Fixture | Required result |
|---|---|
| Tier 5 predecessor merges before tier 10 extension; extension decision/webhook arrives first | Settle predecessor first; allocations 5 and 5, independent of posting/delivery order |
| Proposal 2 -> pilot 5 -> result 10 | Increments 2, 3, 5; total 10 |
| Useful distinct direction without full protocol; another team develops protocol then study | Direction 2, protocol increment 3, study increment 5; original proposer keeps 2 without automatic future shares |
| Same accepted direction later yields a rigorous negative result | Preserve valid direction credit and assess the new study on its actual information value |
| Proposal/pilot/result for one family bundled in a single accepted PR | One tier-10 milestone and 10 total; no ordering by arbitrary file/ID names |
| Tier-5 parser, separate README/tests PRs, distinct tier-10 finding | Parser family total 5; finding may earn 10; packaging adds no automatic credit |
| A 10 plus B 10 at family high-water 20; A reduced to 5 | A 5, B 10 by default; 5 unallocated; no reopened tier or automatic transfer |
| Seed evidence baseline 10, competitive allocation 0; extension to 20 | At most 10 new points |
| Saturated family renamed or policy-migrated | 0 new credit for the rename/migration itself |
| Saturated 20 plus distinct predecessor-linked tier-10 successor | 30 across two justified families; credited evidence cannot overlap |
| Joint 5 split 33.33%/66.67% | 16,665 and 33,335 units; exactly 50,000 total |
| Joint 5 with 40% genuinely disputed | At most 30,000 uncontested units rank; 20,000 withheld; release keeps original period |
| One result tagged into four branches | One award and conserved category total |
| Ten aliases or twenty near-identical proposals for one search | No extra independence, newcomers or duplicated family awards |
| Deliberate regression followed by repair | 0 new net-value credit; separate conduct review where evidenced |
| Source author without GitHub | Scholarly citation required; properly scoped new contributor work is not blocked |
| Zero-credit assessment versus pending review | Different visible terminal/pending states, reasons and appeal links |

Also test alias resolution, stable family settlement, withheld/resolved shares, occupied seed/high-water baselines independent of net balances, no automatic transfer after correction, and replay invariance. Require all applicable fixture pairs to remain invariant under irrelevant changes to prose length, identity display name, AI model label and PR fragmentation.

**7. Period leaderboards and contributor profiles**

Offer all-time, current calendar week, current calendar month, prior-period views, category filters, and a newcomer filter. Weeks begin Monday 00:00 UTC. Months use UTC calendar boundaries. Use half-open intervals `[start, end)` and show exact date ranges and timezone.

Assign each increment exactly one canonical category from the atlas: `sources_history`, `corpus_annotations`, `proposals`, `tools_methods`, `experiments`, `replications_audits`, `research_enablement`, or `publication_synthesis`. A mixed contribution is decomposed by actual outcomes, not duplicated into categories. Additional tags cannot multiply credit; published category totals sum to published overall credit, with reserved units reported separately. Newcomer means the contributor's first nonseed accepted substantive contribution PR merged within the preceding 90 days at the view's `as_of` time. For closed periods use the period end; for a live period use the current observation time. Use the earliest participation across established account aliases. The timestamp is independent of scoring delays and never resets through renaming or revocation.

For an initial award or genuine extension, `earned_at` is the GitHub-server merge timestamp of the associated accepted research PR. `posted_at` is the later score-decision merge timestamp. No score appears until the decision is valid and merged. Delayed awards backfill the original period and are labeled accordingly. Decision PRs, corrections, appeals, and resynchronizations do not refresh the earning date.

Current/restated standings include all valid events known now. Publish immutable weekly/monthly snapshots with `as_of`, ledger commit, and revision metadata. Later corrections create restated views while preserving the original as-known snapshot. Reversals affect the original earning period. An actual new extension has its own research PR earning date. Explain this distinction in the UI and export API.

Sort using exact integer credit units. Give equal scores equal competition ranks (`1, 2, 2, 4`); use stable GitHub ID only for display ordering within ties. Round for display only. Offer award drilldowns showing claimed/awarded points, tier, family, allocation, reviewers, rationale, rubric version, and correction history. Never calculate rankings from unreviewed claims, raw commit counts, or mutable account handles.

Every accepted contributor gets a basic contribution page, subject to publication preferences. Every participant may submit an optional profile PR. Feature a richer story module by default after 20 net awarded contribution points across the canonical categories or a publicly reasoned steward nomination for substantial scientific/service work poorly represented by points. This threshold is a display convention, not scientific status; it does not buy authorship or reviewer privileges. Do not permanently expose someone merely because they once crossed it.

Profile content may include a short bio, optional photo/link, field of interest, ORCID, and an interview-style account of a contribution. Require explicit consent, plain text/sanitized Markdown, approved link schemes, length limits, and a GitHub ownership check. No real name, employer, location, demographic information, or portrait is mandatory. Do not scrape biographies or send invitations automatically. Permit public ranking/story opt-out without erasing the audit record, and explain the persistence of public Git history. Operational account removal and abuse/security reports can use a private channel; they are not alternate research submission paths.
