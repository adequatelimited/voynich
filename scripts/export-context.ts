import { readFile, writeFile } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { hashObject } from '../src/hash.ts';
import { DEFAULT_PROFILE } from '../src/grading.ts';
import type { FamilyRecord } from '../src/contracts.ts';
const families = JSON.parse(await readFile('scoring/families.json', 'utf8')) as FamilyRecord[];
const commit = execFileSync('git', ['-c', `safe.directory=${process.cwd().replaceAll('\\', '/')}`, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim();
const context = { schema_version: '1.0', repository_id: 1359336540, pr_number: 0, head_sha: 'local-uncommitted-candidate', base_sha: commit, rules_version: DEFAULT_PROFILE.rules_version, rubric_version: DEFAULT_PROFILE.rubric_version, evaluator_commit: 'unreleased-working-tree', families, credit_high_water_tiers: Object.fromEntries(families.filter(f => f.seed_baseline !== null).map(f => [f.id, f.seed_baseline])), ledger_digest: await hashObject([]), public_evidence: [], acknowledgment_receipts: [], execution_receipts: [], external_assessment_receipts: [], context_status: 'prelaunch_seed_only_not_an_official_forecast_context', notes: ['No competitive decision exists in this seed context.', 'Current candidate SHA/PR and pinned evaluator release must be supplied by an authenticated official context export before equivalent local/official forecasts.', 'Unassessed seeds remain null and cannot be treated as zero.'] };
await writeFile('grading/context.json', JSON.stringify(context, null, 2) + '\n');
