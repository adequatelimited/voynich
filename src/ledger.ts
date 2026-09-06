import { CATEGORIES, TIERS, type AcceptedMilestone, type Allocation, type Category, type DecisionEvent, type FamilyRecord, type LeaderboardEntry, type PublicAward, type Tier } from './contracts.ts';
import { validateDecision, validateDecisionRecord } from './validation.ts';
import type { DecisionRecord, DecisionPublication } from './contracts.ts';

export class LedgerError extends Error { code: string; constructor(code: string, message: string) { super(message); this.name = 'LedgerError'; this.code = code; } }
const demand: (condition: unknown, code: string, message: string) => asserts condition = (condition, code, message) => { if (!condition) throw new LedgerError(code, message); };
export interface FamilyState { family: FamilyRecord; current_evidence_tier: Tier; credit_high_water_tier: Tier; seed_occupied_units: number; settled_milestones: string[] }
export interface SettledAward { event: DecisionEvent; original_units: number; allocations: Allocation[]; history: string[] }
export interface LedgerState { families: Record<string, FamilyState>; awards: Record<string, SettledAward>; event_ids: string[]; last_sequence: number; public_awards: PublicAward[]; paid_units: number; held_units: number; withdrawn_units: number }
export interface ReplayOptions {
  /** Verify authenticated receipt, delegated policy, model stages, merged bytes and acknowledgments outside this pure engine. */
  verifyDecision?: (event: DecisionEvent) => boolean;
  /** Trusted accepted-research history, not the set of already-posted award files. */
  accepted_milestones?: AcceptedMilestone[];
}
function timestamp(value: string): number { const time = Date.parse(value); demand(Number.isFinite(time) && /Z$/.test(value), 'TIMESTAMP', 'Ledger times must be valid UTC timestamps.'); return time; }
export function materializeDecision(record: DecisionRecord, publication: DecisionPublication, verifyPublication: (record: DecisionRecord, publication: DecisionPublication) => boolean): DecisionEvent {
  demand(validateDecisionRecord(record).valid, 'SCHEMA', 'Malformed immutable decision record.');
  demand(verifyPublication(record, publication), 'PUBLICATION_AUTHORITY', 'Decision publication requires an authenticated GitHub merge receipt and exact signed-file binding.');
  demand(/^[a-f0-9]{40,64}$/.test(publication.merge_sha) && Number.isSafeInteger(publication.pr_number) && publication.pr_number > 0 && !!publication.receipt_ref, 'PUBLICATION', 'Missing decision merge identity.');
  demand(timestamp(publication.merged_at) >= timestamp(record.earned_at), 'TIMESTAMP', 'Decision publication cannot predate the research merge.');
  return { ...record, posted_at: publication.merged_at };
}
function validateAllocation(allocation: Allocation): void {
  demand(Number.isSafeInteger(allocation.units) && allocation.units >= 0, 'ALLOCATION', 'Credit units are nonnegative exact integers.');
  demand((allocation.github_id === undefined) !== (allocation.reservation_id === undefined), 'BENEFICIARY', 'An allocation has exactly one beneficiary or reservation.');
  if (allocation.github_id !== undefined) demand(Number.isSafeInteger(allocation.github_id) && allocation.github_id > 0, 'IDENTITY', 'GitHub account IDs must be positive integers.');
  if (allocation.status === 'paid') demand(allocation.github_id !== undefined && !!allocation.acknowledgment_receipt_ref, 'ACKNOWLEDGMENT', 'Published credit requires authenticated responsibility acknowledgment.');
}
function validateAllocations(allocations: Allocation[], cap: number): number {
  const seen = new Set<string>(); let total = 0;
  for (const a of allocations) { validateAllocation(a); const key = `${a.github_id ?? 'reservation:' + a.reservation_id}`; demand(!seen.has(key), 'DUPLICATE_ALLOCATION', 'A beneficiary appears once in an allocation map.'); seen.add(key); total += a.units; }
  demand(Number.isSafeInteger(total) && total <= cap, 'CONSERVATION', 'An event cannot allocate more than its originally consumed increment.'); return total;
}
function milestoneOrder(a: AcceptedMilestone, b: AcceptedMilestone): number {
  const delta = timestamp(a.earned_at) - timestamp(b.earned_at); if (delta) return delta;
  if (a.depends_on.includes(b.id)) return 1; if (b.depends_on.includes(a.id)) return -1;
  return a.repository_id - b.repository_id || a.pr_number - b.pr_number || a.id.localeCompare(b.id);
}
/** Replay verified append-only events. Receipt authenticity is deliberately never inferred from a field in JSON. */
export function replayLedger(events: DecisionEvent[], registry: FamilyRecord[], options: ReplayOptions = {}): LedgerState {
  const state: LedgerState = { families: {}, awards: {}, event_ids: [], last_sequence: 0, public_awards: [], paid_units: 0, held_units: 0, withdrawn_units: 0 };
  const aliases = new Map<string, string>();
  for (const family of registry) {
    demand(!aliases.has(family.id) && !state.families[family.id], 'FAMILY', `Duplicate family ID: ${family.id}`);
    demand(family.seed_baseline === null || TIERS.includes(family.seed_baseline), 'SEED', 'Invalid seed baseline.');
    demand(family.seed || family.seed_baseline === 0, 'SEED', 'Nonseed families begin with zero occupied tier.');
    state.families[family.id] = { family, current_evidence_tier: family.seed_baseline ?? 0, credit_high_water_tier: family.seed_baseline ?? 0, seed_occupied_units: (family.seed_baseline ?? 0) * 10000, settled_milestones: [] };
    for (const alias of [family.id, ...family.aliases]) { demand(!aliases.has(alias), 'ALIAS', `Ambiguous family alias: ${alias}`); aliases.set(alias, family.id); }
  }
  const canonical = (id: string): string => { const result = aliases.get(id); demand(result, 'FAMILY', `Unknown family: ${id}`); return result; };
  for (const family of registry) for (const predecessor of family.predecessor_family_ids) { demand(canonical(predecessor) !== family.id, 'SUCCESSOR', 'A family cannot be its own predecessor.'); demand(family.excluded_overlap.length, 'SUCCESSOR', 'Successor scopes must explicitly exclude previously credited evidence.'); }
  const visiting = new Set<string>(); const visited = new Set<string>();
  function visit(id: string): void { if (visited.has(id)) return; demand(!visiting.has(id), 'CYCLE', 'Family dependency cycle.'); visiting.add(id); for (const p of state.families[id]!.family.predecessor_family_ids) visit(canonical(p)); visiting.delete(id); visited.add(id); }
  registry.forEach(f => visit(f.id));
  const milestones = [...(options.accepted_milestones ?? [])].sort(milestoneOrder);
  const milestoneIds = new Set<string>(); const prFamilies = new Set<string>();
  for (const m of milestones) { demand(!milestoneIds.has(m.id), 'MILESTONE', 'Duplicate trusted milestone.'); milestoneIds.add(m.id); const key = `${m.repository_id}/${m.pr_number}/${canonical(m.family_id)}`; demand(!prFamilies.has(key), 'MILESTONE', 'One canonical family milestone per accepted PR.'); prFamilies.add(key); }
  const sorted = [...events].sort((a, b) => a.sequence - b.sequence);
  for (const event of sorted) {
    demand(validateDecision(event).valid, 'SCHEMA', `Malformed decision: ${event.id}`);
    demand(options.verifyDecision?.(event) === true, 'AUTHORITY', `Decision lacks verified delegated authority: ${event.id}`);
    demand(event.sequence === state.last_sequence + 1, 'SEQUENCE', 'Missing or duplicate ledger sequence.');
    demand(!state.event_ids.includes(event.id), 'REPLAY', 'Duplicate event ID.');
    demand(timestamp(event.posted_at) >= timestamp(event.earned_at), 'TIMESTAMP', 'Decision cannot precede its research merge.');
    const familyId = canonical(event.family_id); const family = state.families[familyId]!;
    demand(event.rubric_version === family.family.rubric_version, 'POLICY', 'Family rubric is pinned; migration requires an explicit trusted registry migration.');
    demand(!family.family.seed || family.family.seed_baseline !== null, 'UNASSESSED_SEED', 'Resolve this seed baseline before allocating dependent credit.');
    if (['award', 'upgrade', 'assess_zero', 'decline_credit', 'settle_withheld'].includes(event.kind)) {
      const milestone = milestones.find(m => m.id === event.milestone_id);
      demand(milestone, 'MERGE_HISTORY', 'A trusted accepted-research milestone is required.');
      demand(canonical(milestone.family_id) === familyId && milestone.repository_id === event.repository_id && milestone.pr_number === event.pr_number && milestone.earned_at === event.earned_at, 'MERGE_BINDING', 'Decision must bind the trusted research merge, family and original earning date.');
      demand(!family.settled_milestones.includes(event.milestone_id), 'REPLAY', 'This milestone has already settled.');
      for (const previous of milestones) {
        if (previous.id === milestone.id) break;
        if (canonical(previous.family_id) === familyId || milestone.depends_on.includes(previous.id)) demand(Object.values(state.families).some(f => f.settled_milestones.includes(previous.id)), 'PREDECESSOR_PENDING', `Settle earlier accepted milestone ${previous.id} before ${milestone.id}.`);
      }
      for (const dependency of milestone.depends_on) demand(Object.values(state.families).some(f => f.settled_milestones.includes(dependency)), 'PREDECESSOR_PENDING', `Unsettled dependency: ${dependency}`);
      if (event.kind === 'assess_zero' || event.kind === 'decline_credit') demand(event.cumulative_tier === 0 && !event.allocation_shares?.length, 'ZERO', 'Zero/declined decisions cannot allocate credit.');
      const increment = Math.max(0, event.cumulative_tier - family.credit_high_water_tier);
      let allocations: Allocation[] = [];
      if (increment > 0) {
        const shares = event.allocation_shares; demand(shares && shares.reduce((sum, s) => sum + s.share_basis_points, 0) === 10000, 'SHARES', 'All shares, including held reservations, total 10,000 basis points.');
        allocations = shares.map(s => ({ ...(s.github_id !== undefined ? { github_id: s.github_id } : { reservation_id: s.reservation_id! }), units: increment * s.share_basis_points, status: s.status, ...(s.acknowledgment_receipt_ref ? { acknowledgment_receipt_ref: s.acknowledgment_receipt_ref } : {}) }));
        demand(validateAllocations(allocations, increment * 10000) === increment * 10000, 'CONSERVATION', 'New increments are fully allocated or held.');
      } else demand(!event.allocation_shares?.length, 'DUPLICATE_CREDIT', 'No increment is available; do not allocate consumed credit.');
      family.current_evidence_tier = Math.max(family.current_evidence_tier, event.cumulative_tier) as Tier;
      family.credit_high_water_tier = Math.max(family.credit_high_water_tier, event.cumulative_tier) as Tier;
      family.settled_milestones.push(event.milestone_id);
      state.awards[event.id] = { event, original_units: increment * 10000, allocations, history: [event.id] };
    } else {
      const target = event.target_event_id ? state.awards[event.target_event_id] : undefined;
      demand(target, 'CORRECTION_TARGET', 'Corrections target an existing original award.');
      demand(canonical(target.event.family_id) === familyId && target.event.earned_at === event.earned_at && target.event.milestone_id === event.milestone_id && target.event.repository_id === event.repository_id && target.event.pr_number === event.pr_number && target.event.category === event.category, 'CORRECTION_BINDING', 'Corrections preserve the original family, category, research identity and earning date.');
      demand(event.replacement_allocations !== undefined && !event.allocation_shares, 'CORRECTION', 'Corrections publish an explicit replacement allocation map, never a fresh increment.');
      const replacement = event.replacement_allocations; const total = validateAllocations(replacement, target.original_units);
      if (event.kind === 'revoke') demand(total === 0, 'REVOKE', 'Revocation removes the target allocation.');
      if (['release_allocation', 'reassign_attribution'].includes(event.kind)) demand(event.factual_receipt_refs?.length, 'FACTUAL_AUTHORITY', 'Changed attribution/released reservations require authenticated factual/acknowledgment evidence.');
      const oldById = new Map(target.allocations.filter(a => a.github_id !== undefined).map(a => [a.github_id!, a]));
      if (event.kind === 'correct' || event.kind === 'revoke') for (const a of replacement) { const old = a.github_id !== undefined ? oldById.get(a.github_id) : target.allocations.find(x => x.reservation_id === a.reservation_id); demand(old && a.units <= old.units && !(old.status === 'held' && a.status === 'paid'), 'WINDFALL', 'A correction cannot transfer or release credit; use a separately authorized attribution event.'); }
      if (event.kind === 'release_allocation') {
        demand(total === target.allocations.reduce((sum, a) => sum + a.units, 0) && replacement.length === target.allocations.length, 'CONSERVATION', 'Releasing held credit preserves the current allocation map and total.');
        for (const allocation of replacement) {
          const old = target.allocations.find(candidate => allocation.github_id !== undefined ? candidate.github_id === allocation.github_id : candidate.reservation_id === allocation.reservation_id);
          demand(old && old.units === allocation.units && (old.status === allocation.status || (old.status === 'held' && allocation.status === 'paid' && !!allocation.acknowledgment_receipt_ref)), 'RELEASE', 'An acknowledgment releases only the same beneficiary and exact existing units; it never reassigns credit.');
        }
      }
      if (event.kind === 'reassign_attribution') demand(total === target.allocations.reduce((sum, allocation) => sum + allocation.units, 0), 'CONSERVATION', 'Attribution reassignment cannot restore withdrawn units.');
      if (event.kind === 'restore') {
        const originalShares = target.event.allocation_shares ?? [];
        for (const a of replacement) { const original = originalShares.find(s => s.github_id !== undefined ? s.github_id === a.github_id : s.reservation_id === a.reservation_id); demand(original && a.units <= target.original_units * original.share_basis_points / 10000, 'RESTORE', 'Restoration cannot give original credit to a new beneficiary.'); }
      }
      target.allocations = replacement.map(a => ({ ...a })); target.history.push(event.id);
      family.current_evidence_tier = event.cumulative_tier;
      // High-water occupancy never falls, even after revocation/correction.
    }
    state.event_ids.push(event.id); state.last_sequence = event.sequence;
  }
  for (const [id, award] of Object.entries(state.awards)) {
    const current = award.allocations.reduce((sum, a) => sum + a.units, 0); state.withdrawn_units += award.original_units - current;
    for (const allocation of award.allocations) {
      if (allocation.status === 'held') state.held_units += allocation.units;
      else { state.paid_units += allocation.units; if (allocation.units) state.public_awards.push({ id, family_id: canonical(award.event.family_id), github_id: allocation.github_id!, units: allocation.units, earned_at: award.event.earned_at, posted_at: award.event.posted_at, category: award.event.category, pr_number: award.event.pr_number }); }
    }
  }
  const occupied = Object.values(state.families).reduce((sum, f) => sum + f.credit_high_water_tier * 10000 - f.seed_occupied_units, 0);
  demand(state.paid_units + state.held_units + state.withdrawn_units === occupied, 'CONSERVATION', 'Paid, held and withdrawn credit must conserve occupied nonseed value.');
  return state;
}

export function periodBounds(period: 'all' | 'week' | 'month', asOf: string): { start: string | null; end: string | null } {
  const date = new Date(timestamp(asOf)); if (period === 'all') return { start: null, end: null };
  date.setUTCHours(0, 0, 0, 0);
  if (period === 'week') { date.setUTCDate(date.getUTCDate() - (date.getUTCDay() + 6) % 7); const end = new Date(date); end.setUTCDate(end.getUTCDate() + 7); return { start: date.toISOString(), end: end.toISOString() }; }
  date.setUTCDate(1); const end = new Date(date); end.setUTCMonth(end.getUTCMonth() + 1); return { start: date.toISOString(), end: end.toISOString() };
}
export interface LeaderboardOptions { period?: 'all' | 'week' | 'month'; as_of: string; category?: Category; excluded_github_ids?: number[]; identity_aliases?: Record<number, number>; newcomer?: boolean; first_substantive_merge?: Record<number, string> }
export function buildLeaderboard(state: Pick<LedgerState, 'public_awards'>, options: LeaderboardOptions): LeaderboardEntry[] {
  const bounds = periodBounds(options.period ?? 'all', options.as_of); const asOf = timestamp(options.as_of); const entries = new Map<number, LeaderboardEntry>();
  const canonical = (id: number): number => { const seen = new Set<number>(); while (options.identity_aliases?.[id] !== undefined) { demand(!seen.has(id), 'IDENTITY_CYCLE', 'Identity alias cycle.'); seen.add(id); id = options.identity_aliases[id]!; } return id; };
  const excluded = new Set((options.excluded_github_ids ?? []).map(canonical));
  for (const award of state.public_awards) {
    const earned = timestamp(award.earned_at); if (timestamp(award.posted_at) > asOf || earned > asOf) continue;
    if (bounds.start && (earned < timestamp(bounds.start) || earned >= timestamp(bounds.end!))) continue;
    if (options.category && award.category !== options.category) continue;
    const github_id = canonical(award.github_id); if (excluded.has(github_id)) continue;
    if (options.newcomer) {
      const history = Object.entries(options.first_substantive_merge ?? {}).filter(([id]) => canonical(Number(id)) === github_id).map(([, time]) => timestamp(time));
      if (!history.length) continue; const earliest = Math.min(...history); if (earliest > asOf || earliest < asOf - 90 * 86400000) continue;
    }
    let entry = entries.get(github_id); if (!entry) { entry = { github_id, units: 0, points: 0, rank: 0, category_units: Object.fromEntries(CATEGORIES.map(c => [c, 0])) as Record<Category, number> }; entries.set(github_id, entry); }
    entry.units += award.units; entry.category_units[award.category] += award.units; entry.points = entry.units / 10000;
  }
  const sorted = [...entries.values()].sort((a, b) => b.units - a.units || a.github_id - b.github_id);
  let rank = 0; sorted.forEach((entry, i) => { if (i === 0 || sorted[i - 1]!.units !== entry.units) rank = i + 1; entry.rank = rank; }); return sorted;
}
