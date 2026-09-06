# Acceptance evidence

This file records the implementation-stage checks. It deliberately does not certify ranked launch.

- Public TypeScript contracts, schema validation, deterministic ledger and grading orchestration have automated unit coverage. Actual test totals and release commits are recorded with the deployment handoff.
- Ten scientific parser/metric tests passed. The five baseline analyses ran against actual ZL3b data under join/split/strict variants and control corpora. A fresh local Python environment reproduced all scientific result fields; measured CPU time differs normally.
- Real local Cloudflare runtime tests cover durable budget admission and restart recovery, simultaneous duplicate webhooks, raw-body signatures, role separation, bounded dispatch and stored-stage recovery.
- The website passed real desktop/mobile browser journeys, schema-valid manifest download, honest empty leaderboards and disabled-auth behavior. Worker tests additionally cover OAuth/PKCE/session replay and signed projection publication.
- The GitHub App installation is restricted to the public research repository. Authentication and repository identity have been verified by the setup tooling.
- Cloudflare databases, private evidence bucket and review queues have been provisioned. Database migrations have been applied; website publication verification is recorded at deployment.

**Not yet passed:** actual subscription-client inference pilot, official grading calibration, real scored contributor lifecycle, independent human reference calibration, independently performed scientific replication, official seed tiers, and complete visual/binary/execution coverage. No test fixture, second AI persona or local rerun is represented as those forms of evidence.
