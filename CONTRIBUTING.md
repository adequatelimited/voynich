# Contributing to voynich.win

Read [RULES.md](RULES.md), [SCORING.md](SCORING.md) and [GRADING.md](GRADING.md). **No Score Gaming:** improve shared research and claim the corresponding earned credit. Running the public grader, choosing useful work, improving evidence and appealing mistakes are encouraged. Negative findings and unconventional hypotheses receive the same evidence standards.

Ranked intake is active under the published best-effort AI grading profile. Supported contributions receive official scores; calibration remains incomplete.

## Fork, change, submit and revise

1. Choose a question, task, relevant artifact or candidate direction. Check related work/family overlap. A branch or proposal does not reserve future credit.
2. Fork [adequatelimited/voynich](https://github.com/adequatelimited/voynich/fork), clone **your fork**, add upstream and create a branch. Replace `YOUR-HANDLE`.

```sh
git clone https://github.com/YOUR-HANDLE/voynich.git
cd voynich
git remote add upstream https://github.com/adequatelimited/voynich.git
git fetch upstream
git switch -c contribution/my-question upstream/main
pnpm install --frozen-lockfile
```

PowerShell uses the same Git commands and `pnpm.cmd install --frozen-lockfile`.

3. Add artifacts and `contributions/YOUR-ID/contribution.yaml` from [the template](templates/contribution.yaml). Record responsible numeric GitHub IDs, roles, AI use, before/after outcome, evidence, rights, limits and claimed cumulative/incremental points. `gh api user --jq .id` reports your authenticated ID. Never copy a test identity. Use [the direction card](templates/direction.yaml) for suggestions; a qualifying tier-2 direction needs no full protocol or execution.
4. Run deterministic checks. These check metadata/arithmetic, not novelty, scientific truth or legal rights.

```sh
pnpm validate
node src/cli.ts validate --manifest contributions/YOUR-ID/contribution.yaml
```

5. Optionally use current public `grading/context.json` and `grading/profiles/active.json` to run the same pipeline with **your own trusted adapter and expressly authorized allowance**. The default unconfigured profile returns a visible hold and performs no inference.

```sh
pnpm preflight --bundle . --manifest contributions/YOUR-ID/contribution.yaml --context grading/context.json
pnpm grade --bundle . --manifest contributions/YOUR-ID/contribution.yaml --context grading/context.json --profile grading/profiles/active.json --runner /absolute/path/to/your-trusted-runner.mjs --output local-estimate.json
```

An adapter is executable local code: load only your own trusted file. Participant previews do not use the project's shared subscription. An estimate cannot authorize an award. Inspect context/profile compatibility and limitations; exact LLM determinism is not promised. Clearing a cache does not authorize repeated official samples.

6. Review `git diff --cached`, commit the actual artifact directories you changed, push and open a PR against upstream `main`.

```sh
git add research contributions
git commit -m "Add a scoped research contribution"
git push -u origin contribution/my-question
gh pr create --repo adequatelimited/voynich --base main --head YOUR-HANDLE:contribution/my-question --fill
```

Website sign-in and an App installation on your fork are optional for GitHub's own flow.

7. Read the current PR summary and versioned JSON report. It identifies assessed head, rule/gate, evidence, required fix, verification, claimed/expected/proposed points and next action. `gh pr view NUMBER --repo adequatelimited/voynich --comments` retrieves feedback. Use its linked versioned report and verify the head SHA before applying changes.
8. Fix local artifacts, rerun checks, commit and push **the same branch**. Material evidence belongs in committed files. Rapid pushes debounce and consume the published finite review quota; unchanged reruns reuse valid judgments.
9. A sole author with a 100% self-attribution share can acknowledge responsibility using the PR template's explicit rights and responsibility declarations. Otherwise, when requested, post `/voynich-ack MILESTONE-ID RESPONSIBILITY-DIGEST` from your own GitHub account. Confirm the displayed work, shares and contribution terms. This is responsibility/consent, not a vote for points. Missing/disputed shares remain outside rankings and never silently pass to the submitter.
10. Eligible routine work merges after trusted checks. A separate verified decision PR settles credit using the original research merge date. `accepted_score_pending` indicates recoverable pending settlement, not lost/zero credit.

Mechanical conflicts may be repaired only with verified permissions and no force-push. Otherwise the bot supplies a checksummed patch and local commands. Inspect it, verify SHA-256, run `git apply --check patch.diff`, apply, rerun checks and push. Never silently change another person's scientific meaning.

## Browser-only participation

Fork on GitHub. Choose **Add file → Create new file** to copy the direction/contribution templates into the stated paths, replace every example field and add a rights record. Choose **Commit changes → Create a new branch**, then **Contribute → Open pull request** against upstream `main`. The website wizard can generate files; GitHub PRs remain the only research intake. Revise through GitHub on the same fork branch. Actual novice-pilot evidence belongs in launch records; these instructions are not proof that a pilot occurred.

## Evidence, artifacts and credit

Relevant documents, images, datasets, notebooks, tools, code, harnesses and workflows are eligible for their useful outcome. Upload size, code lines, citations, commits and PR counts earn no automatic points. Cite original authors separately from leaderboard beneficiaries; historical source authors need no GitHub account.

Commit third-party bytes only when redistribution is established. Otherwise add an original catalog annotation and canonical reference with honest access/rights status. Large material needs an approved-origin manifest, **actual** SHA-256/byte count, type, provenance, rights and retention. Never invent a checksum for unfetched material. Unknown origins or unsupported formats receive a visible hold. The initial text adapter cannot certify a PDF/image from a filename or OCR alone; relevant full visual inspection requires a configured bounded inspector.

Rights, privacy, safety and honest evidence are universal gates. Missing tier-20 external evidence alone does not block a supported lower tier. External expertise is scientific evidence, distinct from AI point assignment. Routine service, appeals, funding and profiles earn no competitive points; a separately useful reusable capability follows the research route.

## Appeals and contribution terms

Appeal through a linked PR in `governance/appeals/` identifying the artifact/head, disputed criterion and evidence, ordinarily within 30 days; later material evidence may reopen a case. An AI regrade corrects points audibly. Unchanged dissatisfaction is not another random sample. Humans resolve contested facts/rights/attribution/incidents without setting replacement points. Protected changes follow [GOVERNANCE.md](GOVERNANCE.md).

By submitting, certify your authority to contribute under the declared rights, scholarly attribution and AI disclosure, and accept the public review/credit process. Do not include credentials or sensitive private information. Public Git history and clones may persist; see [PRIVACY.md](PRIVACY.md).


## Large research artifacts

Submit unpacked files through the same fork / branch / pull-request workflow. Video and archives/compressed content are prohibited, including ZIP-based documents and renamed payloads. The active v4 profile allows 160 files, 4 MB per original and 24 MB total; full reports/code plus bounded data representations must fit 96 KB of model evidence. Include a concise report explaining provenance, rights, intended use, method and results. Large TXT/CSV/TSV/JSON/JSONL data can use the published deterministic inspection representation; source bytes remain hash-bound in Git. PDF/image inspection is not enabled by this release. Run local preflight with `--profile grading/profiles/active.json`. See GRADING.md for exact coverage and limits.


## Current v5 artifact and response-completeness release

The active profile supports 8,000,000 original bytes per file, 24,000,000 total source bytes and 160 files. Full manifests, rights statements, reports and executable code plus deterministic data views may occupy up to 1,000,000 evidence-content bytes, within a 1,200,000-byte complete stage envelope. Small submissions use only their actual evidence; this is a ceiling, not padding. Sonnet, at most four calls, one active job/session, unchanged qualitative tiers and aggregate operating ceilings remain in force. No usage counters or prior awards reset.

XML joins the UTF-8 data allowlist. The established saxes parser validates the entire document and counts elements, without evaluating code or retrieving external resources. DTDs and entity declarations are prohibited. Video and all archives/compressed containers remain prohibited. Larger datasets retain explicit partial semantic coverage; all code, prose reports, provenance and manifests remain fully supplied. Earlier v4 profiles retain their original evidence allocation through the versioned model_evidence_bytes setting.

Response-completeness instructions prefer concise gate/outcome explanations over redundant informational findings. Every included finding still requires an explicit blocks_merge_or_credit boolean; nothing is inferred or repaired by the server. Invalid prior responses remain immutable and do not authorize points. The new published profile can assess the still-pending evidence afresh; valid judgments under an unchanged profile cannot be rerolled. This release is operator-authorized to clear actual artifact and pipeline blockers and does not claim calibration passed.

