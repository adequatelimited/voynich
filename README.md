# voynich.win

Run the [offline Python research harness](tools/research/README.md), inspect the [actual baseline reports](experiments/baselines/) and review [coverage and gaps](research/coverage-and-gaps.md). The bounded research loop requires no paid AI.

An open human/AI research challenge to decipher the Voynich manuscript and, if it contains recoverable linguistic content, translate it. We collect inspectable evidence, competing explanations, reusable tools and useful research directions. Contribution credit is not scientific truth or a percentage translated.

**Status: building toward a closed pilot. Ranked intake is disabled.** The public grading profile remains unconfigured until a supported subscription runner, explicit usage allowance, actual-model calibration and integration pilot are verified. Synthetic tests do not demonstrate actual-model fairness or scientific independence.

- [Start contributing](CONTRIBUTING.md): fork → branch → artifacts/manifest → PR → AI feedback → revisions → eligible merge → verified credit.
- [Global rules](RULES.md), beginning with **No Score Gaming**; [rubric](SCORING.md); [complete AI methodology](GRADING.md).
- [Research](research/), [source catalog](sources/), [methods](methods/), [starter tasks](research/first-tasks/) and [launch evidence](docs/launch/status.md).
- [Public grading package](grading/README.md), [schemas](schemas/) and [calibration fixtures](grading/fixtures/).

Install Node.js 24 and pnpm 10.28.1. PowerShell uses `pnpm.cmd` when execution policy blocks `pnpm.ps1`.

```sh
git clone https://github.com/adequatelimited/voynich.git
cd voynich
pnpm install --frozen-lockfile
pnpm typecheck
pnpm test
pnpm validate
pnpm build
pnpm projection
```

Local validation needs no model, Cloudflare or App credentials. `@voynich/core` exports portable ESM contracts, validators, exact ledger/period rules, public prompts, preflight and the two-assessor/one-adjudicator pipeline. The private attendant separately verifies authenticated receipts and fresh action authority; contributor JSON cannot mint points.

This is the **public** workspace and canonical research/credit history. Private `adequatelimited/voynich-website` and `adequatelimited/voynich-attendant` contain operational code; all effective merit rules and local assessment methods remain here. Relevant documents, images, datasets, tools, code and harnesses may qualify through demonstrable utility. A useful unique direction can earn 2 before execution; a protocol at 5 adds 3 and a study at 10 adds 5. Upload/PR counts are not scoring units.

Project-authored software uses Apache-2.0, original prose CC BY 4.0 where identified, and original data an explicit per-manifest license. Third-party works retain their rights. See [rights map](LICENSES/README.md), [AI policy](AI_POLICY.md), [authorship](AUTHORSHIP.md), [governance](GOVERNANCE.md) and [privacy](PRIVACY.md).
