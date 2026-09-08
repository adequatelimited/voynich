import { CATEGORIES, TIERS, type Contribution, type ArtifactManifest, type Direction, type StageAssessment, type DecisionEvent, type ValidationIssue, type ValidationResult } from './contracts.ts';

import type { DecisionRecord } from './contracts.ts';
export interface JsonSchema { $schema?: string; $id?: string; type?: string; enum?: readonly unknown[]; properties?: Record<string, JsonSchema>; required?: string[]; additionalProperties?: boolean; items?: JsonSchema; minItems?: number; maxItems?: number; minLength?: number; maxLength?: number; minimum?: number; maximum?: number; pattern?: string }
const text = (maxLength = 12000): JsonSchema => ({ type: 'string', minLength: 1, maxLength });
const id = (): JsonSchema => ({ ...text(160), pattern: '^[a-zA-Z0-9][a-zA-Z0-9._:-]*$' });
const integer = (minimum = 0, maximum = Number.MAX_SAFE_INTEGER): JsonSchema => ({ type: 'integer', minimum, maximum });
const list = (items: JsonSchema, minItems = 0, maxItems = 1000): JsonSchema => ({ type: 'array', items, minItems, maxItems });
const enumeration = (values: readonly unknown[]): JsonSchema => ({ enum: values });
const object = (properties: Record<string, JsonSchema>, required = Object.keys(properties)): JsonSchema => ({ type: 'object', properties, required, additionalProperties: false });
const strings = () => list(text());
const tier = () => enumeration(TIERS);
const shareSchema = object({ github_id: integer(1), reservation_id: id(), share_basis_points: integer(0, 10000) }, ['share_basis_points']);
const allocationSchema = object({ github_id: integer(1), reservation_id: id(), units: integer(), status: enumeration(['paid', 'held']), acknowledgment_receipt_ref: text() }, ['units', 'status']);
const aiSchema = object({ status: enumeration(['none', 'assisted', 'primarily_generated']), tools: list(object({ provider: text(100), model_id: text(200), model_version: text(200), accessed_at: text(40), tasks: strings(), human_verification: text() })), reproducibility_notes: { type: 'string', maxLength: 12000 } });
const outcomeSchema = object({ id: id(), family_id: id(), extends: {}, before: text(), after: text(), acceptance_test: text(), evidence: list(text(1000), 1), related_outcomes: strings(), claimed_cumulative_tier: tier(), claimed_incremental_points: integer(0, 20), claim_rationale: text(), attribution: list(shareSchema, 1, 100) }, ['id', 'family_id', 'before', 'after', 'acceptance_test', 'evidence', 'related_outcomes', 'claimed_cumulative_tier', 'claimed_incremental_points', 'claim_rationale', 'attribution']);
export const contributionSchema: JsonSchema = { $schema: 'https://json-schema.org/draft/2020-12/schema', $id: 'https://voynich.win/schemas/contribution-v1.json', ...object({ schema_version: enumeration(['1.0']), id: id(), kind: enumeration(['research', 'direction', 'artifact', 'profile', 'governance', 'maintenance', 'appeal']), title: text(250), summary: text(4000), branch_ids: strings(), contributors: list(object({ github_id: integer(1), github_login: text(100), roles: list(text(100), 1) }), 1, 100), ai_usage: aiSchema, changes: list(object({ path: text(1000), improvement: text() }), 1), outcomes: list(outcomeSchema), claimed_total_points: integer(), rubric_version: text(100), conflicts: strings(), limitations: strings(), rights_manifest: text(1000), local_estimate_reference: text(1000) }, ['schema_version', 'id', 'kind', 'title', 'summary', 'branch_ids', 'contributors', 'ai_usage', 'changes', 'outcomes', 'claimed_total_points', 'rubric_version', 'conflicts', 'limitations', 'rights_manifest']) };
export const directionSchema: JsonSchema = { $schema: contributionSchema.$schema!, $id: 'https://voynich.win/schemas/direction-v1.json', ...object({ schema_version: enumeration(['1.0']), id: id(), title: text(250), question: text(), rationale: text(), distinctness: text(), prior_work_check: object({ scope: text(), references: strings(), checked_at: text(40) }), first_step: text(), limitations: strings(), attribution: list(text(), 1), branch_ids: strings(), family_id: id(), status: enumeration(['candidate', 'accepted', 'in_progress', 'tested', 'superseded']) }) };
export const artifactSchema: JsonSchema = { $schema: contributionSchema.$schema!, $id: 'https://voynich.win/schemas/artifact-v1.json', ...object({ schema_version: enumeration(['1.0']), id: id(), path: text(1000), origin: text(3000), sha256: { type: 'string', pattern: '^[a-f0-9]{64}$' }, byte_length: integer(), media_type: text(200), source_id: id(), rights: text(), redistribution: enumeration(['permitted', 'reference_only', 'unknown']), state: enumeration(['awaiting_transfer', 'quarantined', 'verified', 'accepted', 'unavailable', 'checksum_mismatch', 'withdrawn']), attribution: text(), retention: text() }, ['schema_version', 'id', 'sha256', 'byte_length', 'media_type', 'source_id', 'rights', 'redistribution', 'state', 'attribution', 'retention']) };
const gateSchema = object({ gate: text(100), status: enumeration(['pass', 'fail', 'unknown']), evidence_refs: strings(), reason: text() });
export const assessmentSchema: JsonSchema = { $schema: contributionSchema.$schema!, $id: 'https://voynich.win/schemas/assessment-v1.json', ...object({ schema_version: enumeration(['1.0']), admission_action: enumeration(['accept', 'accept_unscored', 'needs_revision', 'hold', 'duplicate_consolidated', 'reject']), score_status: enumeration(['proposed', 'unscored', 'held', 'declined']), conduct_status: enumeration(['clear', 'concern', 'restricted_hold']), findings: list(object({ rule_id_or_gate: text(100), severity: enumeration(['info', 'warning', 'blocker']), path_or_locus: text(1000), evidence_refs: strings(), reason: text(), required_change: { type: 'string', maxLength: 12000 }, verification_step: { type: 'string', maxLength: 12000 }, blocks_merge_or_credit: { type: 'boolean' } })), outcomes: list(object({ family_decision: enumeration(['new','extension','duplicate']), family_comparisons: list(object({ family_id: id(), existing_scope: text(), relationship: enumeration(['same_outcome','distinct_outcome']), reason: text() })), source_outcome_ids: strings(), acceptance_test: text(), excluded_overlap: strings(), family_id: id(), scope: text(), category: enumeration(CATEGORIES), predecessors: strings(), aliases: strings(), claimed_tier: tier(), assessed_tier: tier(), gate_evidence: list(gateSchema, 7, 7), attribution_status: enumeration(['verified', 'partially_withheld', 'withheld']), reason: text(), validation_evidence: object({ execution_receipt_refs: strings(), external_assessment_receipt_refs: strings(), independent_inspection_refs: strings() }) }, ['family_id', 'scope', 'category', 'predecessors', 'aliases', 'claimed_tier', 'assessed_tier', 'gate_evidence', 'attribution_status', 'reason'])), inspected_paths: strings(), inspection_gaps: strings(), next_action: text(), appeal_route: text() }) };
export const decisionSchema: JsonSchema = { $schema: contributionSchema.$schema!, $id: 'https://voynich.win/schemas/decision-v1.json', ...object({ schema_version: enumeration(['1.0']), id: id(), sequence: integer(1), kind: enumeration(['award', 'upgrade', 'assess_zero', 'decline_credit', 'settle_withheld', 'release_allocation', 'reassign_attribution', 'correct', 'revoke', 'restore']), family_id: id(), rubric_version: text(100), category: enumeration(CATEGORIES), repository_id: integer(1), pr_number: integer(1), milestone_id: id(), earned_at: text(40), posted_at: text(40), assessment_id: id(), artifact_binding_digest: { type: 'string', pattern: '^[a-f0-9]{64}$' }, authority_receipt_ref: text(1000), cumulative_tier: tier(), allocation_shares: list(object({ ...shareSchema.properties!, status: enumeration(['paid', 'held']), acknowledgment_receipt_ref: text() }, ['share_basis_points', 'status']), 0, 100), target_event_id: id(), replacement_allocations: list(allocationSchema), factual_receipt_refs: strings(), reason: text() }, ['schema_version', 'id', 'sequence', 'kind', 'family_id', 'rubric_version', 'category', 'repository_id', 'pr_number', 'milestone_id', 'earned_at', 'posted_at', 'assessment_id', 'artifact_binding_digest', 'authority_receipt_ref', 'cumulative_tier', 'reason']) };

function walk(value: unknown, schema: JsonSchema, path: string, issues: ValidationIssue[]): void {
  const issue = (code: string, message: string) => issues.push({ path, code, message });
  if (schema.enum && !schema.enum.includes(value)) { issue('enum', 'Value is outside the published allowed values.'); return; }
  if (schema.type === 'object') {
    if (!value || typeof value !== 'object' || Array.isArray(value)) { issue('type', 'Expected an object.'); return; }
    const record = value as Record<string, unknown>;
    for (const key of schema.required ?? []) if (!Object.hasOwn(record, key)) issues.push({ path: `${path}.${key}`, code: 'required', message: 'Required field is missing.' });
    for (const [key, val] of Object.entries(record)) {
      const prop = schema.properties?.[key];
      if (prop) walk(val, prop, `${path}.${key}`, issues);
      else if (schema.additionalProperties === false) issues.push({ path: `${path}.${key}`, code: 'unknown_field', message: 'Unknown fields are not silently ignored.' });
    }
  } else if (schema.type === 'array') {
    if (!Array.isArray(value)) { issue('type', 'Expected an array.'); return; }
    if (value.length < (schema.minItems ?? 0) || value.length > (schema.maxItems ?? Infinity)) issue('length', 'Array length is outside the allowed range.');
    value.forEach((item, i) => walk(item, schema.items ?? {}, `${path}[${i}]`, issues));
  } else if (schema.type === 'string') {
    if (typeof value !== 'string') { issue('type', 'Expected a string.'); return; }
    if (value.length < (schema.minLength ?? 0) || value.length > (schema.maxLength ?? Infinity)) issue('length', 'String length is outside the allowed range.');
    if (schema.pattern && !new RegExp(schema.pattern).test(value)) issue('pattern', 'String does not match the required format.');
  } else if (schema.type === 'integer') {
    if (typeof value !== 'number' || !Number.isSafeInteger(value)) issue('type', 'Expected an exact safe integer.');
    else if (value < (schema.minimum ?? -Infinity) || value > (schema.maximum ?? Infinity)) issue('range', 'Integer is outside the allowed range.');
  } else if (schema.type === 'boolean' && typeof value !== 'boolean') issue('type', 'Expected a boolean.');
}
export function validateSchema<T>(value: unknown, schema: JsonSchema): ValidationResult<T> {
  const issues: ValidationIssue[] = []; walk(value, schema, '$', issues);
  return issues.length ? { valid: false, issues } : { valid: true, value: value as T, issues: [] };
}
export function isSafeRepositoryPath(path: string): boolean {
  return !!path && path.length <= 1000 && !/^[a-zA-Z]:|^[/\\]|[\x00-\x1f\\:]/.test(path) && !path.split('/').some(p => !p || p === '.' || p === '..' || p.toLowerCase() === '.git' || /[. ]$/.test(p) || /^(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)/i.test(p));
}
export function validateContribution(input: unknown): ValidationResult<Contribution> {
  const result = validateSchema<Contribution>(input, contributionSchema); if (!result.valid) return result;
  const value = result.value; const issues: ValidationIssue[] = [];
  const add = (path: string, code: string, message: string) => issues.push({ path, code, message });
  const seen = new Set<string>(); const people = new Set<number>();
  value.contributors.forEach((p, i) => { if (people.has(p.github_id)) add(`contributors[${i}]`, 'duplicate_identity', 'Each responsible account appears once.'); people.add(p.github_id); });
  value.outcomes.forEach((outcome, i) => {
    if (seen.has(outcome.family_id)) add(`outcomes[${i}].family_id`, 'duplicate_family', 'One highest cumulative milestone per family per PR.'); seen.add(outcome.family_id);
    if (outcome.claimed_incremental_points > outcome.claimed_cumulative_tier) add(`outcomes[${i}]`, 'claim_arithmetic', 'An increment cannot exceed the cumulative tier.');
    if (outcome.attribution.reduce((sum, s) => sum + s.share_basis_points, 0) !== 10000) add(`outcomes[${i}].attribution`, 'shares', 'Attribution must total exactly 10,000 basis points, including reservations.');
    const beneficiaries = new Set<string>();
    outcome.attribution.forEach((s, j) => {
      if ((s.github_id === undefined) === (s.reservation_id === undefined)) add(`outcomes[${i}].attribution[${j}]`, 'beneficiary', 'Specify exactly one GitHub ID or reservation ID.');
      if (s.github_id !== undefined && !people.has(s.github_id)) add(`outcomes[${i}].attribution[${j}]`, 'responsibility', 'A proposed beneficiary must be listed among responsible contributors.');
      const key = `${s.github_id ?? 'reservation:' + s.reservation_id}`; if (beneficiaries.has(key)) add(`outcomes[${i}].attribution[${j}]`, 'duplicate_beneficiary', 'Combine a beneficiary into one allocation.'); beneficiaries.add(key);
    });
    for (const path of outcome.evidence) if (!isSafeRepositoryPath(path)) add(`outcomes[${i}].evidence`, 'unsafe_path', 'Evidence must use safe repository-relative paths.');
    if (outcome.extends !== undefined && outcome.extends !== null && typeof outcome.extends !== 'string') add(`outcomes[${i}].extends`, 'type', 'Extends is an outcome ID or null.');
  });
  const total = value.outcomes.reduce((sum, o) => sum + o.claimed_incremental_points, 0);
  if (value.claimed_total_points !== total) add('claimed_total_points', 'claim_arithmetic', 'Claimed total must equal the sum of claimed family increments.');
  for (const path of [...value.changes.map(c => c.path), value.rights_manifest]) if (!isSafeRepositoryPath(path)) add(path, 'unsafe_path', 'Use a safe repository-relative path.');
  if (value.ai_usage.status === 'none' && value.ai_usage.tools.length) add('ai_usage', 'disclosure', 'Status none cannot contain AI tools.');
  if (value.ai_usage.status !== 'none' && !value.ai_usage.tools.length) add('ai_usage', 'disclosure', 'Disclose the tools used; an exposed model version may be unknown.');
  if (['profile', 'governance', 'maintenance', 'appeal'].includes(value.kind) && value.claimed_total_points !== 0) add('claimed_total_points', 'service_only', 'Routine service/governance/profile/appeal records claim zero; submit a separately evidenced capability as research.');
  return issues.length ? { valid: false, issues } : result;
}
export const validateDirection = (input: unknown) => validateSchema<Direction>(input, directionSchema);
export const profileSchema: JsonSchema = { $schema: contributionSchema.$schema!, $id: 'https://voynich.win/schemas/profile-v1.json', ...object({ schema_version: enumeration(['1.0']), github_id: integer(1), github_login: text(100), display_name: text(100), bio: { type: 'string', maxLength: 1200 }, links: list(text(1000), 0, 5), consent: object({ public_profile: { type: 'boolean' }, public_ranking: { type: 'boolean' }, story: { type: 'boolean' } }) }, ['schema_version', 'github_id', 'github_login', 'consent']) };
export const validateProfile = (input: unknown) => validateSchema<import('./contracts.ts').PublicProfile>(input, profileSchema);
export const validateAssessment = (input: unknown) => validateSchema<StageAssessment>(input, assessmentSchema);
export const validateDecision = (input: unknown) => validateSchema<DecisionEvent>(input, decisionSchema);
export const decisionRecordSchema: JsonSchema = { ...decisionSchema, $id: 'https://voynich.win/schemas/decision-record-v1.json', properties: Object.fromEntries(Object.entries(decisionSchema.properties!).filter(([key]) => key !== 'posted_at')), required: decisionSchema.required!.filter(key => key !== 'posted_at') };
export const validateDecisionRecord = (input: unknown) => validateSchema<DecisionRecord>(input, decisionRecordSchema);
export function validateArtifact(input: unknown): ValidationResult<ArtifactManifest> {
  const result = validateSchema<ArtifactManifest>(input, artifactSchema); if (!result.valid) return result;
  const issues: ValidationIssue[] = []; const value = result.value;
  if (!value.path && !value.origin) issues.push({ path: '$', code: 'location', message: 'Supply a repository path or an origin.' });
  if (value.path && !isSafeRepositoryPath(value.path)) issues.push({ path: '$.path', code: 'unsafe_path', message: 'Unsafe artifact path.' });
  if (value.origin) { try { const url = new URL(value.origin); if (url.protocol !== 'https:' || url.username || url.password) throw new Error(); } catch { issues.push({ path: '$.origin', code: 'origin', message: 'Origin must be credential-free HTTPS; retrieval still requires an approved-origin policy.' }); } }
  return issues.length ? { valid: false, issues } : result;
}
