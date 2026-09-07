import test from 'node:test';
import assert from 'node:assert/strict';
import { assessmentsAgree, buildStageRequest, DEFAULT_PROFILE, gradingDigests, MemoryGradingCache, preflight, proposedIncrement, runGrading, validateStageJudgment, type StageRunner } from '../src/grading.ts';
import { validateContribution, validateArtifact, isSafeRepositoryPath } from '../src/validation.ts';
import { sha256 } from '../src/hash.ts';
import { parseRecord } from '../src/cli.ts';
import { assessment, contribution, gradingInput } from './fixtures.ts';
function runner(responses: unknown[] = [assessment(), assessment()]): StageRunner & { calls: string[]; payloads: string[] } { const calls: string[] = []; const payloads: string[] = []; return { calls, payloads, async run(request) { calls.push(request.stage); payloads.push(request.payload); return { text: JSON.stringify(responses[calls.length - 1]), provider: 'anthropic', model: 'synthetic-test-model', exposed_version: 'synthetic-test', usage: { test_calls: 1 }, receipt_ref: `test-receipt-${calls.length}` }; } }; }
test('valid useful direction metadata needs no executed result', () => assert.equal(validateContribution(contribution).valid, true));
test('proposal citation and coverage errors reach one adjudicator while an invalid final cannot award', async () => {
  const input = await gradingInput(); const bad = assessment();
  bad.inspected_paths = [];
  bad.outcomes[0]!.gate_evidence[0]!.evidence_refs = ['invented.md'];
  const model = runner([bad, assessment(), assessment()]);
  assert.equal((await runGrading(input, model)).status, 'complete');
  assert.deepEqual(model.calls, ['assessor', 'adversary', 'adjudicator']);
  assert.ok(model.payloads[2]!.includes('Unknown evidence citation'));
  const rejected = await runGrading(input, runner([bad, assessment(), bad]));
  assert.equal(rejected.status, 'held'); assert.equal(rejected.expected_score, null);
});
test('held provisional tiers may be adjudicated but cannot create credit or bypass final gates', async () => {
  const input = await gradingInput();
  const held = assessment(); held.admission_action = 'needs_revision'; held.score_status = 'held';
  held.outcomes[0]!.gate_evidence[1]!.status = 'unknown';
  assert.deepEqual(validateStageJudgment(held, input), []);
  const stalled = await runGrading(input, runner([held, held]));
  assert.equal(stalled.status, 'held'); assert.equal(stalled.expected_score, null); assert.equal(stalled.official_proposed_score, null);
  const resolved = runner([assessment(), held, assessment()]);
  assert.equal((await runGrading(input, resolved)).status, 'complete');
  assert.deepEqual(resolved.calls, ['assessor', 'adversary', 'adjudicator']);
  const unsafe = structuredClone(held); unsafe.admission_action = 'accept'; unsafe.score_status = 'proposed';
  assert.ok(validateStageJudgment(unsafe, input).length);
  assert.equal((await runGrading(input, runner([assessment(), held, unsafe]))).expected_score, null);
});
test('logical conflicts require adjudication even when both proposals match; final conflicts cannot award', async () => {
  const input = await gradingInput(); const conflicting = assessment(); conflicting.inspection_gaps = ['A stated unresolved limitation.'];
  const model = runner([conflicting, conflicting, assessment()]);
  assert.equal((await runGrading(input, model)).status, 'complete');
  assert.deepEqual(model.calls, ['assessor', 'adversary', 'adjudicator']);
  assert.equal((await runGrading(input, runner([conflicting, conflicting, conflicting]))).expected_score, null);
  const annotated = assessment(); annotated.outcomes[0]!.gate_evidence[0]!.evidence_refs = ['research/example.md (question and first step)'];
  assert.deepEqual(validateStageJudgment(annotated, input), []);
  annotated.outcomes[0]!.gate_evidence[0]!.evidence_refs = ['research/missing.md (question and first step)'];
  assert.ok(validateStageJudgment(annotated, input).some(error => error.startsWith('Unknown evidence citation')));
});
test('malformed shares and claimed totals are rejected before any model', () => { const copy = structuredClone(contribution); copy.outcomes[0]!.attribution[0]!.share_basis_points = 9999; copy.claimed_total_points = 20; const result = validateContribution(copy); assert.equal(result.valid, false); if (!result.valid) assert.deepEqual(result.issues.map(i => i.code), ['shares', 'claim_arithmetic']); });
test('unknown model version is allowed; missing AI disclosure is not', () => { const copy = structuredClone(contribution); copy.ai_usage = { status: 'assisted', tools: [{ provider: 'provider', model_id: 'model', model_version: 'unknown', accessed_at: '2026-09-06', tasks: ['Drafting'], human_verification: 'Inspected the source.' }], reproducibility_notes: 'Version not exposed.' }; assert.equal(validateContribution(copy).valid, true); copy.ai_usage.tools = []; assert.equal(validateContribution(copy).valid, false); });
test('paths reject traversal, Windows devices, drives and alternate data streams', () => { for (const path of ['../secret', 'a/../../b', 'C:/secret', '/secret', 'a\\b', '.git/config', 'a/NUL.txt', 'a/file:secret', 'a/trailing.']) assert.equal(isSafeRepositoryPath(path), false, path); assert.equal(isSafeRepositoryPath('research/folios/f1r.md'), true); });
test('duplicate YAML keys fail instead of changing authority silently', () => assert.throws(() => parseRecord('id: a\nid: b\n'), /Invalid YAML/));
test('artifact link must be HTTPS without embedded credentials', () => { const data = { schema_version: '1.0', id: 'test', origin: 'https://user:secret@example.com/a', sha256: 'a'.repeat(64), byte_length: 1, media_type: 'text/plain', source_id: 'source-test', rights: 'Test only.', redistribution: 'unknown', state: 'awaiting_transfer', attribution: 'Test fixture.', retention: 'Test fixture.' }; assert.equal(validateArtifact(data).valid, false); });
test('unconfigured profile invokes zero model sessions and produces hold', async () => { const input = await gradingInput(); input.profile = DEFAULT_PROFILE; const model = runner(); const report = await runGrading(input, model); assert.equal(model.calls.length, 0); assert.equal(report.status, 'held'); assert.equal(report.expected_score, null); });

test('local previews include the published profile response contract in the bounded stage request', async () => {
  const input = await gradingInput(); input.profile.settings = { response_contract: 'Synthetic public serialization instructions.' };
  const request = await buildStageRequest(input, 'assessor');
  assert.ok(request.developer.endsWith('Synthetic public serialization instructions.'));
  input.profile.max_input_bytes = 1;
  await assert.rejects(() => buildStageRequest(input, 'assessor'), /input_limit/);
});
test('two isolated agreeing stages complete useful suggestion estimate', async () => { const input = await gradingInput(); const model = runner(); const report = await runGrading(input, model); assert.deepEqual(model.calls, ['assessor', 'adversary']); assert.equal(report.expected_score, 2); assert.equal(report.awarded_score, null); assert.equal(model.payloads[1]!.includes('previous_reports'), false); });
test('material disagreement invokes one adjudication and no averaging', async () => { const input = await gradingInput(); const model = runner([assessment(2), assessment(5), assessment(2)]); const report = await runGrading(input, model); assert.deepEqual(model.calls, ['assessor', 'adversary', 'adjudicator']); assert.equal(report.expected_score, 2); });
test('claim20 with valid10 evidence gets10 and cannot mandate expert point approval', async () => { const input = await gradingInput(); input.contribution.outcomes[0]!.claimed_cumulative_tier = 20; input.contribution.outcomes[0]!.claimed_incremental_points = 20; input.contribution.claimed_total_points = 20; const model = runner([assessment(10), assessment(10)]); const report = await runGrading(input, model); assert.equal(report.expected_score, 10); assert.equal(report.status, 'complete'); });
test('nonseed current10 upgradedto20 forecasts10 ratherthan20', async () => { const input = await gradingInput(); input.context.credit_high_water_tiers['family-test'] = 10; assert.equal(proposedIncrement(assessment(20), input.context), 10); delete input.context.credit_high_water_tiers['family-test']; assert.throws(() => proposedIncrement(assessment(20), input.context), /Missing current family/); });
test('identical evidence/newhead/claim-only revision reuses firstsuccessful stages', async () => { const input = await gradingInput(); const cache = new MemoryGradingCache(); const model = runner(); const before = await runGrading(input, model, cache); input.context.head_sha = 'e'.repeat(40); input.contribution.claimed_total_points = 5; input.contribution.outcomes[0]!.claimed_cumulative_tier = 5; input.contribution.outcomes[0]!.claimed_incremental_points = 5; const after = await runGrading(input, model, cache); assert.equal(model.calls.length, 2); assert.equal(before.merit_evidence_digest, after.merit_evidence_digest); assert.notEqual(before.artifact_binding_digest, after.artifact_binding_digest); assert.equal(after.expected_score, 2); assert.equal(after.claimed_score, 5); });
test('substantive changed evidence has a new merit identity', async () => { const input = await gradingInput(); const before = await gradingDigests(input); input.files[0]!.content += ' Material new discriminating evidence.'; input.files[0]!.sha256 = await sha256(input.files[0]!.content!); input.files[0]!.byte_length = new TextEncoder().encode(input.files[0]!.content).byteLength; assert.notEqual(before.merit_evidence_digest, (await gradingDigests(input)).merit_evidence_digest); });
test('code/manuscript whitespace is not stripped for grade lottery prevention', async () => { const input = await gradingInput(); const before = await gradingDigests(input); input.files[0]!.sha256 = await sha256('a b'); const middle = await gradingDigests(input); input.files[0]!.sha256 = await sha256('ab'); assert.notEqual(middle.merit_evidence_digest, (await gradingDigests(input)).merit_evidence_digest); assert.notEqual(before.merit_evidence_digest, middle.merit_evidence_digest); });
test('PDF/image and unsupported artifacts produce an inspection hold before inference', async () => { const input = await gradingInput(); input.files[0]!.media_type = 'application/pdf'; const model = runner(); const result = await runGrading(input, model); assert.equal(model.calls.length, 0); assert.ok(result.holds.some(x => x.includes('inspection_gap'))); });
test('invalid file digests and credentials are deterministic restricted holds', async () => { const input = await gradingInput(); input.files[0]!.sha256 = '0'.repeat(64); input.files[1]!.content = '-----BEGIN PRIVATE KEY-----'; const issues = await preflight(input); assert.ok(issues.some(x => x.code === 'integrity')); assert.ok(issues.some(x => x.code === 'restricted_content')); assert.ok(issues.every(x => !x.message.includes('BEGIN PRIVATE'))); });
test('proposed policy changes cannot grade or deploy themselves', async () => { const input = await gradingInput(); input.files[0]!.path = 'grading/prompts/system.md'; const issues = await preflight(input); assert.ok(issues.some(x => x.code === 'protected_path')); });
test('incomplete inspection and fabricated citations cannot mint a judgment', async () => { const input = await gradingInput(); const value = assessment(); value.inspected_paths = []; value.outcomes[0]!.gate_evidence[0]!.evidence_refs = ['invented.md']; const errors = validateStageJudgment(value, input); assert.ok(errors.some(x => x.includes('Incomplete coverage'))); assert.ok(errors.some(x => x.includes('Unknown evidence'))); });
test('positive tier with unknown universal rights gate is rejected', async () => { const input = await gradingInput(); const value = assessment(); value.outcomes[0]!.gate_evidence[1]!.status = 'unknown'; assert.ok(validateStageJudgment(value, input).some(x => x.includes('all universal gates'))); });
test('invalid output does not trigger model repair loops', async () => { const input = await gradingInput(); let calls = 0; const report = await runGrading(input, { async run() { calls++; return { text: 'not JSON', provider: 'anthropic', model: 'synthetic-test-model', exposed_version: 'test', usage: {}, receipt_ref: 'test' }; } }); assert.equal(calls, 1); assert.equal(report.status, 'held'); assert.equal(report.expected_score, null); });
test('runtime substitution fails closed', async () => { const input = await gradingInput(); const report = await runGrading(input, { async run() { return { text: JSON.stringify(assessment()), provider: 'anthropic', model: 'unapproved-cheaper-model', exposed_version: 'test', usage: {}, receipt_ref: 'test' }; } }); assert.ok(report.holds[0]!.startsWith('runtime_identity')); });
test('blind stage request refuses earlier report andadjudicator requiresboth', async () => { const input = await gradingInput(); await assert.rejects(() => buildStageRequest(input, 'adversary', [assessment()]), /cannot see/); await assert.rejects(() => buildStageRequest(input, 'adjudicator', []), /exactly two/); });
test('gate and scope disagreement remains material', () => { const first = assessment(); const second = assessment(); second.outcomes[0]!.scope += ' Expanded question.'; assert.equal(assessmentsAgree(first, second), false); });
test('actual assessed20 requires trusted external evidence, not two AI personas', async () => { const input = await gradingInput(); const value = assessment(20); assert.ok(validateStageJudgment(value, input).some(x => x.includes('Tier 20'))); value.outcomes[0]!.validation_evidence = { execution_receipt_refs: [], external_assessment_receipt_refs: ['external-test-receipt'], independent_inspection_refs: [] }; input.context.external_assessment_receipts = ['external-test-receipt']; assert.equal(validateStageJudgment(value, input).length, 0); });


test('four-stage profile preserves malformed proposals and corrects missing final fields once', async () => {
  const input = await gradingInput(); input.profile.max_stages = 4;
  const held = assessment(); held.admission_action = 'needs_revision'; held.score_status = 'held';
  held.findings = [{ rule_id_or_gate: 'G2', severity: 'blocker', path_or_locus: 'research/example.md', evidence_refs: ['research/example.md'], reason: 'Missing evidence.', required_change: 'Supply evidence.', verification_step: 'Inspect evidence.', blocks_merge_or_credit: true }];
  const malformed = structuredClone(held) as any; delete malformed.findings[0].blocks_merge_or_credit;
  const model = runner([null, assessment(), malformed, held]); const cache = new MemoryGradingCache();
  const result = await runGrading(input, model, cache);
  assert.equal(result.assessment?.admission_action, 'needs_revision'); assert.equal(result.expected_score, null);
  assert.deepEqual(model.calls, ['assessor', 'adversary', 'adjudicator', 'corrector']);
  assert.ok(model.payloads[3]!.includes('blocks_merge_or_credit'));
  assert.ok(!model.payloads[1]!.includes('previous_reports'));
  await runGrading(input, model, cache); assert.equal(model.calls.length, 4, 'All raw first responses, including malformed ones, must be cached.');
});
test('bounded correction may remove a false receipt claim but cannot create evidence or improve merit', async () => {
  const input = await gradingInput(); input.profile.max_stages = 4;
  const invalid = assessment(); invalid.outcomes[0]!.validation_evidence = { execution_receipt_refs: ['research/example.md'], external_assessment_receipt_refs: [], independent_inspection_refs: [] };
  const result = await runGrading(input, runner([invalid, assessment(), invalid, assessment()]));
  assert.equal(result.status, 'complete'); assert.equal(result.expected_score, 2); assert.equal(result.stages.length, 4);
  const inflation = await runGrading(input, runner([invalid, assessment(), invalid, assessment(5)]));
  assert.equal(inflation.expected_score, null); assert.ok(inflation.holds.some(x => x.includes('increase')));
  const stillInvalid = runner([invalid, assessment(), invalid, invalid]);
  assert.equal((await runGrading(input, stillInvalid)).expected_score, null); assert.equal(stillInvalid.calls.length, 4);
});
test('correction cannot promote held admission, release credit or erase an existing blocker', async () => {
  const input = await gradingInput(); input.profile.max_stages = 4;
  const held = assessment(); held.admission_action = 'hold'; held.score_status = 'held';
  held.outcomes[0]!.validation_evidence = { execution_receipt_refs: ['fake'], external_assessment_receipt_refs: [], independent_inspection_refs: [] };
  const result = await runGrading(input, runner([held, assessment(), held, assessment()]));
  assert.equal(result.expected_score, null); assert.ok(result.holds.some(x => x.includes('cannot promote')));
});
test('a valid final judgment cannot buy a correction and every gate and receipt namespace is checked', async () => {
  const input = await gradingInput(); input.profile.max_stages = 4;
  const model = runner(); assert.equal((await runGrading(input, model)).status, 'complete'); assert.equal(model.calls.length, 2);
  await assert.rejects(buildStageRequest(input, 'corrector', [assessment(), assessment(), assessment()]), /invalid final/);
  const repeated = assessment(); repeated.outcomes[0]!.gate_evidence.push(repeated.outcomes[0]!.gate_evidence[0]!);
  assert.ok(validateStageJudgment(repeated, input).some(x => x.includes('Exactly one')));
  const falseExpert = assessment(); falseExpert.outcomes[0]!.validation_evidence = { execution_receipt_refs: [], external_assessment_receipt_refs: ['fake'], independent_inspection_refs: [] };
  assert.ok(validateStageJudgment(falseExpert, input).some(x => x.includes('External assessment')));
});

test('independent outcome mapping binds new families to real claims and participates in agreement', async () => {
 const input=await gradingInput(); input.profile.settings.outcome_scope='independent-results-v1';
 const proposal=assessment(); assert.ok(validateStageJudgment(proposal,input).some(e=>e.includes('source_outcome_ids')));
 proposal.outcomes[0]!.source_outcome_ids=[input.contribution.outcomes[0]!.id]; proposal.outcomes[0]!.acceptance_test='Inspect the distinct diagnostic finding'; proposal.outcomes[0]!.excluded_overlap=['Previously credited reusable harness'];
 assert.deepEqual(validateStageJudgment(proposal,input),[]);
 const other=structuredClone(proposal);other.outcomes[0]!.acceptance_test='A different result';assert.equal(assessmentsAgree(proposal,other),false);
 proposal.outcomes[0]!.source_outcome_ids=['invented-claim'];assert.ok(validateStageJudgment(proposal,input).some(e=>e.includes('source_outcome_ids')));
});
