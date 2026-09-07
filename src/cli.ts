#!/usr/bin/env node
import { inspectTextArtifact, artifactBudgets } from './artifacts.ts';
import { readFile, readdir, lstat, mkdir, writeFile, open } from 'node:fs/promises';
import { resolve, join, relative, extname, dirname } from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { parseDocument, stringify } from 'yaml';
import type { Contribution, EvidenceFile, GradingContext, GradingProfile, StageAssessment, StageReceipt } from './contracts.ts';
import { validateContribution, validateDirection, validateArtifact, isSafeRepositoryPath } from './validation.ts';
import { DEFAULT_PROFILE, preflight, runGrading, type GradingCache, type GradingInput, type StageRunner } from './grading.ts';
import { sha256 } from './hash.ts';

export function parseRecord(text: string, path = 'record.yaml'): unknown {
  if (extname(path) === '.json') return JSON.parse(text);
  const document = parseDocument(text, { uniqueKeys: true }); if (document.errors.length) throw new Error(`Invalid YAML in ${path}: ${document.errors[0]!.message}`);
  return document.toJS({ maxAliasCount: 20 });
}
export async function safeRead(root: string, path: string, maxBytes = 1000000): Promise<Buffer> {
  if (!isSafeRepositoryPath(path)) throw new Error(`Unsafe repository path: ${path}`);
  let cursor = resolve(root);
  for (const piece of path.split('/')) { cursor = join(cursor, piece); const info = await lstat(cursor); if (info.isSymbolicLink()) throw new Error(`Symlinks are not admissible: ${path}`); }
  const info = await lstat(cursor); if (!info.isFile() || info.size > maxBytes) throw new Error(`Unavailable or oversized file: ${path}`);
  return readFile(cursor);
}
const mediaType = (path: string) => ({ '.md': 'text/markdown', '.txt': 'text/plain', '.yaml': 'application/yaml', '.yml': 'application/yaml', '.json': 'application/json', '.csv': 'text/csv', '.py': 'text/x-python', '.ts': 'text/typescript', '.js': 'text/javascript' }[extname(path)] ?? 'application/octet-stream');
export async function loadBundle(root: string, manifestPath: string, context: GradingContext, profile: GradingProfile): Promise<GradingInput> {
  const parsed = parseRecord((await safeRead(root, manifestPath)).toString('utf8'), manifestPath); const checked = validateContribution(parsed); if (!checked.valid) throw new Error(JSON.stringify(checked.issues));
  const contribution = checked.value;
  const paths = new Set([manifestPath, contribution.rights_manifest, ...contribution.changes.map(c => c.path), ...contribution.outcomes.flatMap(o => o.evidence)]);
  if (paths.size > profile.max_files) throw new Error('Bundle exceeds the public file limit.');
  const files: EvidenceFile[] = [];
  const budgets = profile.settings.artifact_handling === 'bounded-text-v1' ? artifactBudgets(await Promise.all([...paths].map(async path => ({ path, byte_length: (await lstat(resolve(root, path))).size })))) : new Map<string, number>();
  for (const path of paths) {
    const bytes = await safeRead(root, path, profile.max_file_bytes); const media_type = mediaType(path);
    if (profile.settings.artifact_handling === 'bounded-text-v1') { files.push(await inspectTextArtifact(path, bytes, budgets.get(path)!)); continue; }
    let content: string | undefined; try { content = new TextDecoder('utf-8', { fatal: true }).decode(bytes); } catch { /* Mark unsupported, never silently replace bytes. */ }
    const supported = media_type !== 'application/octet-stream' && content !== undefined;
    files.push({ path, sha256: await sha256(bytes), byte_length: bytes.length, media_type, inspection: supported ? 'complete' : 'unsupported', ...(content !== undefined ? { content } : {}) });
  }
  const packageRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
  const policy = { rules: await readFile(join(packageRoot, 'RULES.md'), 'utf8'), rubric: await readFile(join(packageRoot, 'SCORING.md'), 'utf8'), methodology: await readFile(join(packageRoot, 'GRADING.md'), 'utf8') };
  return { contribution, manifest_path: manifestPath, files, context, profile, policy, mode: 'local_estimate' };
}
class FileCache implements GradingCache {
  readonly directory: string;
  constructor(directory: string) { this.directory = directory; }
  async get(key: string) { try { return JSON.parse(await readFile(join(this.directory, `${await sha256(key)}.json`), 'utf8')) as { assessment: StageAssessment; receipt: StageReceipt }; } catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return undefined; throw error; } }
  async putIfAbsent(key: string, value: { assessment: StageAssessment; receipt: StageReceipt }) { await mkdir(this.directory, { recursive: true }); let file; try { file = await open(join(this.directory, `${await sha256(key)}.json`), 'wx', 0o600); await file.writeFile(JSON.stringify(value)); } catch (error) { if ((error as NodeJS.ErrnoException).code !== 'EEXIST') throw error; } finally { await file?.close(); } }
}
async function records(root: string, subdirectory: string): Promise<string[]> {
  const results: string[] = [];
  async function scan(path: string): Promise<void> { let entries; try { entries = await readdir(path, { withFileTypes: true }); } catch (error) { if ((error as NodeJS.ErrnoException).code === 'ENOENT') return; throw error; } for (const entry of entries) { const child = join(path, entry.name); if (entry.isSymbolicLink()) throw new Error('Repository records cannot contain symlinks.'); if (entry.isDirectory()) await scan(child); else if (/\.(?:json|ya?ml)$/.test(entry.name)) results.push(relative(root, child).replaceAll('\\', '/')); } }
  await scan(join(root, subdirectory)); return results;
}
export async function validateRepository(root: string): Promise<{ checked: number; errors: { path: string; message: string }[] }> {
  const errors: { path: string; message: string }[] = []; let checked = 0; const ids = new Set<string>();
  for (const [directory, validator] of [['contributions', validateContribution], ['research/directions', validateDirection], ['data/manifests', validateArtifact]] as const) {
    for (const path of await records(root, directory)) {
      if (directory === 'contributions' && !/\/contribution\.(?:json|ya?ml)$/.test(path)) continue;
      try { const data = parseRecord((await safeRead(root, path)).toString('utf8'), path); const result = validator(data); checked++; if (!result.valid) errors.push({ path, message: JSON.stringify(result.issues) }); else { if (ids.has(result.value.id)) errors.push({ path, message: 'Duplicate record ID.' }); ids.add(result.value.id); } } catch (error) { errors.push({ path, message: (error as Error).message }); }
    }
  }
  return { checked, errors };
}
async function main(): Promise<void> {
  const args = process.argv.slice(2); const command = args.shift() ?? 'help'; const value = (name: string) => { const index = args.indexOf(name); return index >= 0 ? args[index + 1] : undefined; };
  if (command === 'validate-repository') { const result = await validateRepository(resolve(value('--root') ?? '.')); process.stdout.write(JSON.stringify(result, null, 2) + '\n'); if (result.errors.length) process.exitCode = 1; return; }
  if (command === 'validate') { const path = value('--manifest'); if (!path) throw new Error('Supply --manifest path.'); const result = validateContribution(parseRecord(await readFile(path, 'utf8'), path)); process.stdout.write(JSON.stringify(result, null, 2) + '\n'); if (!result.valid) process.exitCode = 1; return; }
  if (command === 'grade' || command === 'preflight') {
    const root = resolve(value('--bundle') ?? '.'); const manifest = value('--manifest'); const contextPath = value('--context'); if (!manifest || !contextPath) throw new Error('Supply --bundle repository-root --manifest contributions/id/contribution.yaml --context grading-context.json.');
    const context = parseRecord(await readFile(contextPath, 'utf8'), contextPath) as GradingContext;
    const profilePath = value('--profile'); const profile = profilePath ? parseRecord(await readFile(profilePath, 'utf8'), profilePath) as GradingProfile : DEFAULT_PROFILE;
    const input = await loadBundle(root, manifest, context, profile);
    if (command === 'preflight') { const issues = await preflight(input); process.stdout.write(JSON.stringify({ status: issues.length ? 'held' : 'passed', issues }, null, 2) + '\n'); if (issues.length) process.exitCode = 2; return; }
    let runner: StageRunner | undefined; const runnerPath = value('--runner');
    if (runnerPath) { const loaded = await import(pathToFileURL(resolve(runnerPath)).href) as { default?: StageRunner }; runner = loaded.default; if (!runner || typeof runner.run !== 'function') throw new Error('Explicit local runner module must export default { run(request) }. Use only your own trusted adapter.'); }
    const result = await runGrading(input, runner, new FileCache(resolve(value('--cache') ?? '.grading-cache'))); const output = JSON.stringify(result, null, 2) + '\n'; const outputPath = value('--output'); if (outputPath) await writeFile(outputPath, output); else process.stdout.write(output); if (result.status === 'held') process.exitCode = 2; return;
  }
  if (command === 'template') { const template = await readFile(new URL('../templates/contribution.yaml', import.meta.url), 'utf8'); process.stdout.write(template); return; }
  process.stdout.write('voynich validate-repository | validate --manifest FILE | preflight|grade --bundle ROOT --manifest PATH --context FILE [--profile FILE] [--runner TRUSTED_MODULE] [--output FILE]\nNo model is invoked by default. Exit 2 denotes a visible hold, not a score of zero.\n');
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) main().catch(error => { process.stderr.write(`${(error as Error).message}\n`); process.exitCode = 1; });
