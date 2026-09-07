# Fully AI calibration

Launch exception: the [founding AI-scored pilot](releases/2026-09-07-ai-pilot.md) authorizes best-effort scored operation before this larger study is complete. This procedure remains the target evaluation; launch does not convert missing runs into passes.

Calibration and contribution grading are best effort and fully AI operated. No human reference panel or human score approval is required. Only Sonnet is used for these model runs. Agreement is evidence of rubric consistency, not proof of scientific truth, fairness or independent expert validation. Separate contexts of the same model can share errors.

## Frozen AI references

1. Prepare at least 36 synthetic boundary cases covering contribution routes, useful artifacts and directions, duplicate/fragmented claims, missing evidence and prohibited/allowed content. Add cases until all required boundaries are covered. Authored proposed answers remain unverified drafts.
2. Pin the complete evidence, family state, public rubric, prompts and Sonnet profile. Give an assessor and a blind adversary separate fresh contexts with the same evidence. Neither sees the other's answer or draft reference labels. Each applies the published assessment procedure and returns the required evidence-linked judgment.
3. Compare the complete judgments: families/scopes, tiers, G1–G7, incremental credit, allocation digest, admission and conduct. If identical, freeze that reference. If they disagree, run at most one adjudicator against the same evidence and both reports. Freeze only a valid resolved judgment; missing evidence or invalid/unresolved output leaves the case incomplete. Never average scores or reroll for a preferred answer.
4. Record actual unique run/context IDs, model ID, profile/context/fixture/prompt digests, completion times, original receipt references, rationales and the reference freeze time. Verify these against original model receipts and immutable stored inputs through automated checks. A supplied string is not proof of execution.
5. Freeze references before evaluation starts. Never count a reference-generation call as an evaluation call. Never revise reference answers to fit observed failures. A necessary correction produces a new documented reference/method version and separate evaluation cohort, retaining old failures.

## Evaluation and release

Run at least three independent local-preview/official-pipeline pairs per case, using identical public profile, evidence and family state within each pair and matching the frozen reference profile/context. Reference labels and previous trial answers stay outside trial prompts. Record all attempts, including invalid responses, holds and failures. These are evaluation runs; they award no research points and cannot reopen production assessments.

The numerical targets remain:

| Check | Minimum |
|---|---|
| Exact tier agreement with frozen AI references | 80% |
| Within one adjacent tier of AI references | 95% |
| Preview/official agreement on families, tiers and incremental points, each measured separately | 90% |
| Preview/official tiers within one adjacent tier | 95% |
| Deterministic allocation given identical judgments | 100% |
| Explicit critical allowed/prohibited boundaries and deterministic invariants | 100% |

Evaluate each contribution route as well as pooled results. Publish denominators, uncertainty intervals, gate/scope agreement, false/missed conduct flags, repeated-result stability, latency and observed resource use. Missing/unresolved pairs fail rather than disappearing from denominators. Same-model consistency cannot measure all systematic mistakes; report that limitation and test held-out variants before publishing their labels.

Automated integration checks must also establish the actual feedback/revision/merge/decision/leaderboard lifecycle, trusted receipts, exact-head action checks and resource controls. Calibration does not require recruiting human reviewers or additional contributors; use authorized accounts and actual existing PRs where appropriate, and label simulated journeys honestly. A passing offline report cannot itself enable a deployment or mint points.

Corrections remain versioned AI regrades with recorded evidence and deterministic arithmetic. Uncertainty gets a bounded explanation or evidence request, without creating a mandatory human-review appointment. Evidence of execution, rights, attribution and consent must still be real; an AI role or consensus cannot fabricate it.
