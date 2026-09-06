# Contributing to voynich.win

Read [RULES.md](RULES.md), [SCORING.md](SCORING.md) and [GRADING.md](GRADING.md). **No Score Gaming:** improve shared research and claim the corresponding earned credit. Running the public grader, choosing useful work, improving evidence and appealing mistakes are encouraged. Negative findings and unconventional hypotheses receive the same evidence standards.

Ranked intake remains disabled until live-model and integration gates pass. You can prepare inspectable research now; the prelaunch package promises no points.

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
9. When requested, post `/voynich-ack MILESTONE-ID RESPONSIBILITY-DIGEST` from your own GitHub account. Confirm the displayed work, shares and contribution terms. This is responsibility/consent, not a vote for points. Missing/disputed shares remain outside rankings and never silently pass to the submitter.
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
