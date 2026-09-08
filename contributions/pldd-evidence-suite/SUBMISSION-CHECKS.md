# Submission checks

Prepared 2026-09-08 UTC against upstream commit
`b470c129462ca22845371ec9a57c84bccc24af25`.

## Research package

The [package verification record](../../experiments/pldd-evidence-suite/verification/record.json)
and its linked logs retain all attempted checks. The current full test run has
**101 passed, zero failures, zero errors**. The first test run's H007 runtime
metadata mismatch is preserved, with the publication-only comparison change
and actual old/new runtime values disclosed.

All nine frozen analysis entry points were executed. Eight rebuilt every output
byte-identically. H007's sole observed JSON difference is the author-control
Python version, 3.12.13 versus 3.12.14; pandas remains 2.2.3. Its retained golden
hash, actual rebuilt report and exact JSON delta are supplied. Scientific
results, control outputs and evaluation gates are unchanged.

The source comparison audit verifies all 20 included raw inputs and 14 frozen
protocol/audit notes byte-for-byte. The output inventory is
[`SHA256SUMS.txt`](../../experiments/pldd-evidence-suite/SHA256SUMS.txt).
The upstream automatic text attributes would normalize the Naibbe CSV's CRLF
line endings during initial staging. Its original blob was therefore staged
explicitly without filters; all 122 staged file blobs were compared with their
local bytes. A fresh `git checkout-index` extraction reproduces the CSV's
pinned SHA-256 `4e7cfd54b7ec66515d39a51e11ec97e8e19b643b0b189124eebc3982e707dcec`.
Neither the raw file nor the shared Git attributes were changed.
Separate AI agents reviewed package scope, original-source comparisons and
publication claims. This is ordinary local execution/inspection evidence,
not independent human replication or authenticated external receipts.

## Repository metadata and artifact validation

The repository's pinned dependency lockfile was installed with lifecycle scripts
disabled. Actual local validation runtime: Node.js 26.0.0 and pnpm 11.19.0.
No trusted grader, policy, workflow, source registry or lockfile was changed.

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm validate
node src/cli.ts validate --manifest contributions/pldd-evidence-suite/contribution.yaml
pnpm preflight --bundle . --manifest contributions/pldd-evidence-suite/contribution.yaml --context grading/context.json --profile grading/profiles/active.json
```

Repository validation and contribution-schema validation pass. The complete
published artifact inspector reads every declared file and reports no file,
format, size, hash-integrity, secret-pattern, evidence-budget or protected-path
issue. It uses the unchanged active profile, including deterministic partial
semantic representations for large data; this is not a full semantic scan or
malware certification.

**The full local preflight is held**, with the sole issue `policy_mismatch`.
The unchanged exported `grading/context.json` at this base has no root
`rules_version` or `rubric_version` properties; the active profile and
contribution specify `0.1`. The exact output is in [preflight.json](preflight.json).
No grading configuration was edited to remove this hold. The site's official
review must construct its own authenticated current context. No optional paid
model preview, forecast, assessment receipt or score is represented here.

Changes are limited to the contribution's own directory and isolated scientific
package under `experiments/`. The package is below the active 160-file,
8,000,000-byte-per-file and 24,000,000-byte-total limits. Every outgoing file is
enumerated in the contribution manifest; raw inputs and complete result files
are included rather than represented only by a link or uninspected filename.
