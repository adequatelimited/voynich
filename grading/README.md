# The public qualitative grading package

`src/grading.ts` is the executable method used by local previews and imported by the private attendant. Exported `SYSTEM_PROMPT` and `STAGE_PROMPTS` are the actual runtime instructions; `grading/prompts/` is generated from them by `node scripts/export-contracts.ts`. The profile, schemas, full rules/rubric/methodology and immutable evidence are supplied together. No private merit prompt or arbitrary score field is permitted.

The [active profile](profiles/active.json) describes the founding Sonnet AI-scored pilot. [Its release record](releases/2026-09-07-ai-pilot.md) states the authorization, runtime boundaries and incomplete calibration status. The package performs no inference without an explicitly supplied runner and compatible enabled profile. It never extracts subscription credentials, purchases overage or silently switches to API billing.

The runtime sequence is deterministic preflight → assessor → blind adversary → one adjudicator only on material disagreement → output/evidence validation → proposed deterministic increment. Official receipt authentication and current repository authority are verified by the separate broker before action or settlement. A local estimate has `awarded_score: null` forever.

## Portable API

```ts
import {
  validateContribution, preflight, runGrading,
  buildStageRequest, assessmentsAgree, validateStageJudgment,
  finalizeAssessments, proposedIncrement, replayLedger, buildLeaderboard
} from '@voynich/core';
```

`runGrading(input, runner, cache)` supports bounded local execution. Durable official coordinators use `buildStageRequest` and persist independent stage results across requests, then `finalizeAssessments`. A `StageRunner` returns structured raw JSON, actual provider/model/version, usage and an externally authenticated receipt reference. It receives an abort signal, finite byte/time/output limits, no tools or write tokens. Cancellation/timeout may still consume allowance; the attendant retains uncertain reservation exposure and does not automatically repeat that invocation.

Exactly one successful response per immutable merit/stage is retained. A callback/module is trusted local code chosen explicitly by its participant/operator, never read from the incoming PR. The core cannot enforce a provider's complete account quota itself; admission reservations, fencing, shared account headroom and global hard limits live in the private controller before any session starts.

## Evidence and reuse

`artifact_binding_digest` includes exact candidate bytes, manifest, head/base and current context/profile/policy. `merit_evidence_digest` excludes head/PR identity and only explicit score-claim fields/local estimate references from the parsed contribution manifest. JSON object-key ordering is canonicalized; scientific text, manuscript spacing and code whitespace are preserved. The canonical contribution path is `contributions/<id>/contribution.yaml`. Material summary/rationale/evidence changes are not assumed cosmetic. Cross-PR paraphrases require bounded semantic overlap review and public family adjudication; a hash is not a universal novelty detector.

The initial adapter inspects bounded UTF-8 text, Markdown, JSON/YAML, CSV, Python and JavaScript/TypeScript as inert evidence. It **does not execute code** and does not claim to inspect PDF/image/archive/binary visual contents. Unsupported artifacts, missing bytes, incorrect hashes, truncation or incomplete context are explicit holds. OCR alone cannot prove full visual inspection. Legitimate source catalog references can describe unfetched content honestly without claiming the underlying bytes were inspected. Expanded artifact/vision support needs a public calibrated profile/inspector and trusted bounded receipts before activation.

Seven universal gates G1-G7 require evidence refs. Positive credit requires all pass; the highest fully supported tier is chosen, not an average. Genuine independent execution and external expertise remain required where the anchor says so; two AI contexts cannot manufacture them. Every claimed family requires semantic overlap consideration, and independently useful omitted outcomes may be identified. Current public `credit_high_water_tiers`, including aliases and seed occupancy, determine estimates; missing existing-family state is a hold, not a zero assumption.

## Calibration and truthful status

`grading/fixtures/` contains explicitly synthetic, **unreviewed draft boundaries**, never production awards. They need frozen references from two blind Sonnet contexts, at most one adjudicator on disagreement, separate actual evaluation trials and retained receipts. No human reference calibrators or human calibration approval are required. Same-model agreement is best-effort rubric consistency, not expert validation or scientific truth. See [the full AI procedure](calibration.md). Targets: deterministic/critical boundary fixtures 100%; AI-reference exact tier ≥80%, adjacent tier ≥95%. Separate matched local/official forecast trials require ≥3 independent pairs per case, ≥90% exact family/tier/increment agreement, ≥95% adjacent tier and 100% arithmetic agreement. Report route failures, uncertainty widths, denominators, false flags and usage/latency; do not select lucky runs.

No target is claimed achieved by unit tests. Missing calibration, configured model/allowance, complete artifact support, external-fork/joint attribution pilot or operator coverage stays explicit in launch status.
