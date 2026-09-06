import test from 'node:test';
import assert from 'node:assert/strict';
import { materializeDecision, replayLedger } from '../src/ledger.ts';
import { validateDecisionRecord } from '../src/validation.ts';
import { gradingDigests } from '../src/grading.ts';
import { event, family, gradingInput, trusted } from './fixtures.ts';
test('signed decision omits unknowable future posting time; authenticated merge supplies it', () => { const source = event(1, 5); const { posted_at: _, ...record } = source; assert.equal(validateDecisionRecord(record).valid, true); assert.equal(validateDecisionRecord(source).valid, false); const publication = { merged_at: '2026-10-01T00:00:00Z', merge_sha: 'a'.repeat(40), pr_number: 20, receipt_ref: 'authenticated-test-publication' }; assert.throws(() => materializeDecision(record, publication, () => false), /authenticated GitHub/); const materialized = materializeDecision(record, publication, () => true); assert.equal(materialized.posted_at, publication.merged_at); assert.equal(materialized.earned_at, source.earned_at); });
test('unrelated base SHA update changes action binding without buying a new merit sample', async () => { const input = await gradingInput(); const before = await gradingDigests(input); input.context.base_sha = 'e'.repeat(40); const after = await gradingDigests(input); assert.notEqual(before.artifact_binding_digest, after.artifact_binding_digest); assert.equal(before.merit_evidence_digest, after.merit_evidence_digest); });
test('unscored duplicate cannot lower an existing family evidence tier', () => { const events = [event(1, 10), event(2, 0)]; assert.equal(replayLedger(events, [family()], trusted(events)).families['family-test']!.current_evidence_tier, 10); });
