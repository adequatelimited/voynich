import JSON5 from 'json5';
import { SaxesParser } from 'saxes';
import { fileTypeFromBuffer } from 'file-type';
import { parse as parseCSV } from 'csv-parse/sync';
import type { EvidenceFile } from './contracts.ts';
import { sha256 } from './hash.ts';

export const ARTIFACT_METHOD = 'bounded-text-v1';
export const MAX_ARTIFACT_BYTES = 8_000_000;
export const MAX_ARTIFACT_TOTAL = 24_000_000;
export const MODEL_EVIDENCE_BYTES = 96_000;
// Manifests, prose reports and executable source remain fully visible to the AI.
export function canSummarize(path: string): boolean { return /\.(?:txt|csv|tsv|jsonl|ndjson|json|xml)$/i.test(path) && !/(?:^|\/)(?:contribution\.json|rights[^/]*|profiles\/|manifests\/)/i.test(path); }
export function artifactBudgets(files: Array<{ path: string; byte_length: number }>, limit = MODEL_EVIDENCE_BYTES): Map<string, number> {
  if (!Number.isSafeInteger(limit) || limit < 96000 || limit > 1000000) throw new Error('artifact_invalid_model_budget');
  const ordered = [...files].sort((a, b) => a.path.localeCompare(b.path, 'en'));
  const budgets = new Map(ordered.map(f => [f.path, canSummarize(f.path) && f.byte_length > 8000 ? 2000 : f.byte_length]));
  let remaining = limit - [...budgets.values()].reduce((a, b) => a + b, 0);
  if (remaining < 0) throw new Error('model_evidence_limit: full manifests, reports and code plus artifact summaries exceed the published model evidence budget');
  const large = ordered.filter(f => budgets.get(f.path)! < f.byte_length);
  for (let i = 0; i < large.length; i++) {
    const file = large[i]!, current = budgets.get(file.path)!;
    const extra = Math.min(file.byte_length - current, Math.floor(remaining / (large.length - i)), 64000 - current);
    budgets.set(file.path, current + extra); remaining -= extra;
  }
  return budgets;
}
const archives = /\.(?:zip|zipx|tar|tgz|gz|gzip|bz2|bzip2|tbz2?|xz|txz|lz|lzma|lzo|zst|zstd|tzst|br|rar|7z|cab|arj|ace|cpio|ar|a|deb|rpm|iso|dmg|wim|vhd|vhdx|squashfs|sit|sitx|lzh|lha|z|jar|war|ear|apk|ipa|whl|egg|nupkg|docx|xlsx|pptx|odt|ods|odp|epub|npz|kmz|svgz)(?:\.|$)/i;
const videos = /\.(?:mp4|m4v|mov|qt|avi|mkv|webm|flv|f4v|wmv|asf|mpg|mpeg|mpe|m2v|vob|ogv|ogg|3gp|3g2|mts|m2ts|mxf|rm|rmvb|swf|gif|apng)(?:\.|$)/i;
export function excludedArtifact(path: string, bytes?: Uint8Array): string | null {
  if (archives.test(path)) return 'archive_content_prohibited';
  if (videos.test(path)) return 'video_content_prohibited';
  if (!bytes) return null;
  const start = Array.from(bytes.subarray(0, 8), b => b.toString(16).padStart(2, '0')).join('');
  // Reject these before file-type can examine archive members. Nothing is unpacked.
  if (/^(504b(?:0304|0506|0708)|1f8b|425a68|fd377a585a00|377abcaf271c|526172211a07|28b52ffd|213c617263683e)/.test(start)
    || new TextDecoder().decode(bytes.subarray(257, 262)) === 'ustar') return 'archive_content_prohibited';
  return null;
}
const textPath = /\.(?:txt|md|csv|tsv|xml|json|jsonl|ndjson|ya?ml|toml|ini|py|r|js|mjs|cjs|ts|tsx|jsx|c|h|cpp|rs|go|jl|ipynb|bib|tex)$/i;
const secret = /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9_]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{40,}\b|\bsk-ant-[A-Za-z0-9_-]{32,}\b/;
function samples(bytes: Uint8Array, budget: number): Array<{ start_byte: number; end_byte: number; text: string }> {
  const width = Math.max(16, Math.floor(budget / 24));
  const result: Array<{ start_byte: number; end_byte: number; text: string }> = [];
  for (let i = 0; i < 5; i++) {
    let start = Math.floor((bytes.length - width) * i / 4);
    while (start < bytes.length && (bytes[start]! & 0xc0) === 0x80) start++;
    let end = Math.min(bytes.length, start + width);
    while (end < bytes.length && (bytes[end]! & 0xc0) === 0x80) end--;
    result.push({ start_byte: start, end_byte: end, text: new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes.subarray(start, end)) });
  }
  return result;
}
/** Inert full-byte structural inspection with an explicitly partial model representation. */
export async function inspectTextArtifact(path: string, bytes: Uint8Array, textBudget = 64_000): Promise<EvidenceFile> {
  if (!Number.isSafeInteger(textBudget) || textBudget < 0 || textBudget > 1000000) throw new Error('artifact_invalid_budget');
  const prohibited = excludedArtifact(path, bytes); if (prohibited) throw new Error(prohibited);
  if (bytes.length > MAX_ARTIFACT_BYTES) throw new Error('artifact_storage_limit');
  let kind: Awaited<ReturnType<typeof fileTypeFromBuffer>>;
  try { kind = await fileTypeFromBuffer(bytes.subarray(0, 8192)); } catch { throw new Error('artifact_signature_unreadable'); }
  if (kind && kind.ext !== 'xml') {
    if (kind.mime.startsWith('video/') || videos.test(`x.${kind.ext}`)) throw new Error('video_content_prohibited');
    if (archives.test(`x.${kind.ext}`) || /(?:zip|gzip|compress|archive|tar|rar|7z)/i.test(kind.mime)) throw new Error('archive_content_prohibited');
    throw new Error('artifact_format_requires_isolated_inspection');
  }
  if (!textPath.test(path) && !/(?:^|\/)(?:LICENSE|NOTICE|README|Makefile)$/.test(path)) throw new Error('artifact_format_unsupported');
  let text: string;
  try { text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(bytes); } catch { throw new Error('artifact_not_utf8'); }
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]/.test(text)) throw new Error('artifact_binary_controls');
  if (secret.test(text)) throw new Error('restricted_secret_artifact');
  if (/data:(?:video\/|application\/(?:zip|gzip|x-(?:tar|rar|7z)))/i.test(text)) throw new Error('embedded_prohibited_artifact');
  const structure: Record<string, unknown> = { lines: text.split('\n').length, utf8_valid: true, secret_scan: 'entire source', execution_performed: false };
  if (/\.xml$/i.test(path) || kind?.ext === 'xml') {
    if (/<!\s*(?:DOCTYPE|ENTITY)/i.test(text)) throw new Error('artifact_xml_dtd_prohibited');
    let elements = 0; const parser = new SaxesParser({ xmlns: true });
    parser.on('opentag', () => { elements++; });
    parser.on('error', () => { throw new Error('artifact_invalid_xml'); });
    parser.on('doctype', () => { throw new Error('artifact_xml_dtd_prohibited'); });
    parser.write(text).close(); structure.elements = elements;
  } else if (/\.(?:json|ipynb)$/.test(path)) {
    let value: unknown;
    try { value = JSON.parse(text.replace(/^\uFEFF/, '')); }
    catch {
      if (!/\b(?:Infinity|NaN)\b/.test(text) || /\.ipynb$/i.test(path)) throw new Error('artifact_invalid_json');
      try { value = JSON5.parse(text); structure.format = 'scientific_json5'; } catch { throw new Error('artifact_invalid_json'); }
      let nonfinite = 0; const pending: unknown[] = [value];
      while (pending.length) { const item = pending.pop(); if (typeof item === 'number' && !Number.isFinite(item)) nonfinite++; else if (item && typeof item === 'object') for (const child of Object.values(item)) pending.push(child); }
      structure.nonfinite_values = nonfinite;
    }
    structure.json_type = Array.isArray(value) ? 'array' : typeof value;
    structure.json_entries = Array.isArray(value) ? value.length : value && typeof value === 'object' ? Object.keys(value).length : 1;
    if (/\.ipynb$/i.test(path)) {
      const notebook = value as { cells?: Array<{ attachments?: unknown; outputs?: Array<{ data?: Record<string, unknown> }> }> };
      if (!Array.isArray(notebook.cells) || notebook.cells.some(cell => cell.attachments || cell.outputs?.some(output => output.data && Object.keys(output.data).some(type => type !== 'text/plain')))) throw new Error('notebook_embedded_content_unsupported');
    }
  } else if (/\.(?:jsonl|ndjson)$/i.test(path)) {
    let records = 0;
    for (const line of text.split('\n')) if (line.trim()) { try { JSON.parse(line); records++; } catch { throw new Error('artifact_invalid_jsonl'); } }
    structure.records = records;
  } else if (/\.(?:csv|tsv)$/i.test(path)) {
    let rows = 0, maxColumns = 0;
    try { parseCSV(text, { delimiter: /\.tsv$/.test(path) ? '\t' : ',', relax_column_count: true, max_record_size: 64_000,
      on_record: (record: string[]) => { rows++; maxColumns = Math.max(maxColumns, record.length); if (record.length > 4096) throw new Error('columns'); return null; } }); }
    catch { throw new Error('artifact_invalid_or_excessive_csv_record'); }
    Object.assign(structure, { rows, max_columns: maxColumns });
  }
  const sourceHash = await sha256(bytes);
  if (bytes.length <= textBudget) return { path, sha256: sourceHash, byte_length: bytes.length, media_type: 'text/plain', content: text, inspection: 'complete' };
  if (!canSummarize(path)) throw new Error('artifact_requires_full_text_budget');
  // JSON escaping can expand excerpts; adapt the excerpts, never misstate coverage.
  let budget = Math.max(512, textBudget);
  let content = '';
  for (let attempt = 0; attempt < 8; attempt++) {
    content = JSON.stringify({ method: ARTIFACT_METHOD, source_path: path, source_sha256: sourceHash, source_bytes: bytes.length, structure,
      coverage: 'Full source bytes were structurally inspected; the AI receives only deterministic excerpts. This is not full semantic review, malware certification, independent execution, or scientific verification.',
      excerpts: samples(bytes, budget) });
    if (new TextEncoder().encode(content).length <= textBudget) break;
    budget = Math.floor(budget / 2);
  }
  const representationBytes = new TextEncoder().encode(content).length;
  if (representationBytes > textBudget) throw new Error('artifact_representation_budget');
  return { path, sha256: sourceHash, byte_length: bytes.length, media_type: 'text/plain', content, inspection: 'derived',
    representation: { method: ARTIFACT_METHOD, sha256: await sha256(content), byte_length: representationBytes, text_budget: textBudget, coverage: 'structural_full_semantic_partial' } };
}
