import { readFile, readdir, mkdir, writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
import { parseRecord } from '../src/cli.ts';
import { DEFAULT_PROFILE } from '../src/grading.ts';
import type { PublicProjection } from '../src/contracts.ts';
async function collect(directory: string): Promise<Record<string, unknown>[]> {
  const output: Record<string, unknown>[] = []; let entries; try { entries = await readdir(directory, { withFileTypes: true }); } catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return output; throw error; }
  for (const entry of entries) {
    if (entry.isSymbolicLink()) throw new Error('Projection does not follow symlinks.'); const path = join(directory, entry.name);
    if (entry.isDirectory()) output.push(...await collect(path)); else if (/\.(?:json|ya?ml)$/.test(entry.name)) {
      const parsed = parseRecord(await readFile(path, 'utf8'), path);
      if (Array.isArray(parsed)) output.push(...parsed.filter(x => x && typeof x === 'object'));
      else if (parsed && typeof parsed === 'object') { const record = parsed as Record<string, unknown>; const collection = Object.values(record).find(value => Array.isArray(value) && value.some(x => x && typeof x === 'object' && 'id' in x)); if (record.id) output.push(record); else if (collection) output.push(...collection as Record<string, unknown>[]); }
    }
  }
  return output.sort((a, b) => String(a.id ?? a.title).localeCompare(String(b.id ?? b.title)));
}
let repository_commit = 'uncommitted'; try { repository_commit = execFileSync('git', ['-c', `safe.directory=${process.cwd().replaceAll('\\', '/')}`, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(); const changes = execFileSync('git', ['-c', `safe.directory=${process.cwd().replaceAll('\\', '/')}`, 'status', '--porcelain'], { encoding: 'utf8' }).trim(); if (changes) repository_commit += '+working-tree'; } catch { /* Explicitly uncommitted, never invent a release. */ }
const decisions = await collect('governance/decisions'); if (decisions.length) throw new Error('Signed decisions exist: use the authenticated attendant projection export, not the unsigned seed snapshot builder.');
const snapshot: PublicProjection = { schema_version: '1.0', generated_at: new Date().toISOString(), repository_commit, status: 'prelaunch', branches: await collect('research/branches'), sources: await collect('sources'), tasks: await collect('research/first-tasks'), methods: await collect('methods'), directions: await collect('research/directions'), claims: await collect('research/claims'), experiments: await collect('experiments/baselines'), leaderboard: [], awards: [], grading: { profile_id: DEFAULT_PROFILE.id, status: DEFAULT_PROFILE.status, ranked_intake_enabled: false }, gaps: ['Ranked intake awaits a configured bounded subscription runner, actual-model calibration and the real integration pilot.', 'This seed projection contains no competitive awards. It cannot ingest unsigned contributor decisions.'] };
await mkdir('public', { recursive: true }); await writeFile('public/projection.json', JSON.stringify(snapshot, null, 2) + '\n');
process.stdout.write(JSON.stringify({ sources: snapshot.sources.length, branches: snapshot.branches.length, tasks: snapshot.tasks.length, methods: snapshot.methods.length, awards: 0 }) + '\n');
