/** Public wire contracts. All official writes require separately verified authority. */
export const SCHEMA_VERSION = '1.0' as const;
export const TIERS = [0, 2, 5, 10, 20] as const;
export type Tier = typeof TIERS[number];
export const CATEGORIES = ['sources_history', 'corpus_annotations', 'proposals', 'tools_methods', 'experiments', 'replications_audits', 'research_enablement', 'publication_synthesis'] as const;
export type Category = typeof CATEGORIES[number];
export type AdmissionAction = 'accept' | 'accept_unscored' | 'needs_revision' | 'hold' | 'duplicate_consolidated' | 'reject';
export type ScoreStatus = 'proposed' | 'unscored' | 'held' | 'declined';
export interface Contributor { github_id: number; github_login: string; roles: string[] }
export interface AttributionShare { github_id?: number; reservation_id?: string; share_basis_points: number }
export interface AIUsage {
  status: 'none' | 'assisted' | 'primarily_generated';
  tools: { provider: string; model_id: string; model_version: string; accessed_at: string; tasks: string[]; human_verification: string }[];
  reproducibility_notes: string;
}
export interface OutcomeClaim {
  id: string; family_id: string; extends?: string | null; before: string; after: string;
  acceptance_test: string; evidence: string[]; related_outcomes: string[];
  claimed_cumulative_tier: Tier; claimed_incremental_points: number; claim_rationale: string;
  attribution: AttributionShare[];
}
export interface Contribution {
  schema_version: '1.0'; id: string; kind: 'research' | 'direction' | 'artifact' | 'profile' | 'governance' | 'maintenance' | 'appeal';
  title: string; summary: string; branch_ids: string[]; contributors: Contributor[]; ai_usage: AIUsage;
  changes: { path: string; improvement: string }[]; outcomes: OutcomeClaim[];
  claimed_total_points: number; rubric_version: string; conflicts: string[]; limitations: string[]; rights_manifest: string;
  local_estimate_reference?: string;
}
export interface ArtifactManifest {
  schema_version: '1.0'; id: string; path?: string; origin?: string; sha256: string;
  byte_length: number; media_type: string; source_id: string; rights: string;
  redistribution: 'permitted' | 'reference_only' | 'unknown';
  state: 'awaiting_transfer' | 'quarantined' | 'verified' | 'accepted' | 'unavailable' | 'checksum_mismatch' | 'withdrawn';
  attribution: string; retention: string;
}
export interface Direction {
  schema_version: '1.0'; id: string; title: string; question: string; rationale: string;
  distinctness: string; prior_work_check: { scope: string; references: string[]; checked_at: string };
  first_step: string; limitations: string[]; attribution: string[]; branch_ids: string[]; family_id: string;
  status: 'candidate' | 'accepted' | 'in_progress' | 'tested' | 'superseded';
}
export interface FamilyRecord {
  id: string; rubric_version: string; scope: string; acceptance_test: string; aliases: string[];
  predecessor_family_ids: string[]; excluded_overlap: string[]; seed: boolean; seed_baseline: Tier | null;
}
export interface AcceptedMilestone { id: string; family_id: string; repository_id: number; pr_number: number; earned_at: string; depends_on: string[] }
export interface Allocation {
  github_id?: number; reservation_id?: string; units: number; status: 'paid' | 'held'; acknowledgment_receipt_ref?: string;
}
export interface DecisionEvent {
  schema_version: '1.0'; id: string; sequence: number;
  kind: 'award' | 'upgrade' | 'assess_zero' | 'decline_credit' | 'settle_withheld' | 'release_allocation' | 'reassign_attribution' | 'correct' | 'revoke' | 'restore';
  family_id: string; rubric_version: string; category: Category; repository_id: number; pr_number: number;
  milestone_id: string; earned_at: string; posted_at: string; assessment_id: string;
  artifact_binding_digest: string; authority_receipt_ref: string; cumulative_tier: Tier;
  allocation_shares?: (AttributionShare & { status: 'paid' | 'held'; acknowledgment_receipt_ref?: string })[];
  target_event_id?: string; replacement_allocations?: Allocation[]; factual_receipt_refs?: string[]; reason: string;
}
/** Immutable premerge file: actual decision posting time is supplied by authenticated publication metadata. */
export type DecisionRecord = Omit<DecisionEvent, 'posted_at'>;
export interface DecisionPublication { merged_at: string; merge_sha: string; pr_number: number; receipt_ref: string }
export interface GateJudgment { gate: string; status: 'pass' | 'fail' | 'unknown'; evidence_refs: string[]; reason: string }
export interface Finding {
  rule_id_or_gate: string; severity: 'info' | 'warning' | 'blocker'; path_or_locus: string;
  evidence_refs: string[]; reason: string; required_change: string; verification_step: string;
  blocks_merge_or_credit: boolean;
}
export interface OutcomeAssessment {
  family_id: string; scope: string; category: Category; predecessors: string[]; aliases: string[];
  claimed_tier: Tier; assessed_tier: Tier; gate_evidence: GateJudgment[];
  attribution_status: 'verified' | 'partially_withheld' | 'withheld'; reason: string;
  validation_evidence?: { execution_receipt_refs: string[]; external_assessment_receipt_refs: string[]; independent_inspection_refs: string[] };
}
export interface StageAssessment {
  schema_version: '1.0'; admission_action: AdmissionAction; score_status: ScoreStatus;
  conduct_status: 'clear' | 'concern' | 'restricted_hold'; findings: Finding[];
  outcomes: OutcomeAssessment[]; inspected_paths: string[]; inspection_gaps: string[];
  next_action: string; appeal_route: string;
}
export interface EvidenceFile { path: string; sha256: string; byte_length: number; media_type: string; content?: string; inspection: 'complete' | 'derived' | 'unsupported' | 'unavailable'; representation?: { method: 'bounded-text-v1'; sha256: string; byte_length: number; text_budget: number; coverage: 'structural_full_semantic_partial' }; receipt_ref?: string }
export interface GradingContext {
  schema_version: '1.0'; repository_id: number; pr_number: number; head_sha: string; base_sha: string;
  rules_version: string; rubric_version: string; evaluator_commit: string;
  families: FamilyRecord[]; credit_high_water_tiers: Record<string, Tier>; ledger_digest: string; public_evidence: EvidenceFile[];
  acknowledgment_receipts: string[]; execution_receipts: string[];
  external_assessment_receipts?: string[];
}
export interface GradingProfile {
  schema_version: '1.0'; id: string; status: 'unconfigured' | 'calibration' | 'active';
  provider: string; model_id: string | null; exposed_version: string; runtime: string;
  rules_version: string; rubric_version: string; max_stages: 3 | 4; max_attempts_per_stage: 1;
  max_input_bytes: number; max_output_bytes: number; max_duration_ms: number;
  max_files: number; max_file_bytes: number; max_total_bytes: number;
  settings: Record<string, string | number | boolean | null>; tool_access: 'none';
}
export type GradingStage = 'assessor' | 'adversary' | 'adjudicator' | 'corrector';
export interface StageReceipt {
  stage: GradingStage; provider: string; model: string; exposed_version: string;
  prompt_digest: string; response_digest: string; started_at: string; completed_at: string;
  usage: Record<string, number | string | null>; receipt_ref: string;
}
export interface GradingReport {
  schema_version: '1.0'; assessment_id: string; artifact_binding_digest: string; merit_evidence_digest: string;
  repository_id: number; pr_number: number; head_sha: string; base_sha: string;
  rules_version: string; rubric_version: string; grading_profile: string; evaluator_commit: string;
  mode: 'local_estimate' | 'official_proposal'; status: 'complete' | 'held';
  claimed_score: number; expected_score: number | null; official_proposed_score: number | null; awarded_score: null;
  assessment: StageAssessment | null; stages: StageReceipt[]; disagreements: string[];
  holds: string[]; reused_assessment_id: string | null;
}
export interface ValidationIssue { path: string; code: string; message: string }
export type ValidationResult<T> = { valid: true; value: T; issues: [] } | { valid: false; issues: ValidationIssue[] };
export interface PublicProjection {
  schema_version: '1.0'; generated_at: string; repository_commit: string; status: 'prelaunch' | 'active' | 'held';
  branches: Record<string, unknown>[]; sources: Record<string, unknown>[]; tasks: Record<string, unknown>[];
  methods: Record<string, unknown>[]; directions: Record<string, unknown>[]; claims: Record<string, unknown>[];
  experiments: Record<string, unknown>[]; leaderboard: LeaderboardEntry[]; awards: PublicAward[];
  profiles?: PublicProfile[]; participation?: { github_id: number; github_login: string; first_substantive_merge_at: string; established_alias_ids: number[] }[];
  grading: { profile_id: string; status: string; ranked_intake_enabled: boolean }; gaps: string[];
}
export interface PublicProfile { schema_version?: '1.0'; github_id: number; github_login: string; display_name?: string; bio?: string; links?: string[]; consent: { public_profile: boolean; public_ranking: boolean; story: boolean }; first_contribution_at?: string }
export interface PublicAward { id: string; family_id: string; github_id: number; github_login?: string; first_contribution_at?: string; units: number; earned_at: string; posted_at: string; category: Category; pr_number: number }
export interface LeaderboardEntry { github_id: number; units: number; points: number; rank: number; category_units: Record<Category, number> }
