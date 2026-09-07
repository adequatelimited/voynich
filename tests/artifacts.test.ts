import test from 'node:test';
import assert from 'node:assert/strict';
import { gzipSync } from 'node:zlib';
import { inspectTextArtifact, artifactBudgets } from '../src/artifacts.ts';
import { sha256 } from '../src/hash.ts';
import { preflight } from '../src/grading.ts';
import { gradingInput } from './fixtures.ts';
const bytes = (text: string) => new TextEncoder().encode(text);
test('large multibyte corpus has reproducible bounded excerpts bound to every original byte', async () => {
  const source = bytes('Manuscript comparison: \u00e9\u6f22\n'.repeat(30000));
  const view = await inspectTextArtifact('data/corpus.txt', source, 4000);
  assert.equal(view.inspection, 'derived'); assert.equal(view.sha256, await sha256(source)); assert.ok(bytes(view.content!).length <= 4000);
  assert.deepEqual(view, await inspectTextArtifact('data/corpus.txt', source, 4000));
  const parsed = JSON.parse(view.content!); assert.equal(parsed.source_bytes, source.length);
  for (const excerpt of parsed.excerpts) assert.equal(new TextDecoder().decode(source.slice(excerpt.start_byte, excerpt.end_byte)), excerpt.text);
  const changed = source.slice(); changed[0] = 65;
  assert.notEqual((await inspectTextArtifact('data/corpus.txt', changed, 4000)).sha256, view.sha256);
});
test('prohibited archive/video extensions and renamed gzip/zip/video content cannot pass as text', async () => {
  for (const ext of ['zip','tar','gz','gzip','rar','7z','xz','bz2','zst','docx','xlsx','epub','npz','mp4','webm','avi','gif','apng']) await assert.rejects(inspectTextArtifact(`x.${ext}`, bytes('ordinary text')), /prohibited/);
  for (const source of [gzipSync(bytes('ordinary text')), Uint8Array.from([80,75,3,4,0,0,0,0]), Uint8Array.from([0,0,0,24,102,116,121,112,109,112,52,50,0,0,0,0,109,112,52,50,0,0,0,0])]) await assert.rejects(inspectTextArtifact('renamed.txt', source), /prohibited/);
});
test('all-byte secret and malformed-data scans include unsampled content', async () => {
  await assert.rejects(inspectTextArtifact('data.txt', bytes('a'.repeat(100000) + ' sk-ant-' + 'x'.repeat(40) + ' b'.repeat(100000)), 2000), /restricted_secret/);
  await assert.rejects(inspectTextArtifact('data.json', bytes('[1,broken]')), /invalid_json/);
  await assert.rejects(inspectTextArtifact('data.jsonl', bytes('{"a":1}\ninvalid')), /invalid_jsonl/);
  const csv = await inspectTextArtifact('data.csv', bytes('a,b\n1,2\n'.repeat(10000)), 2000);
  assert.equal(JSON.parse(csv.content!).structure.rows, 20000);
});
test('code, rights and manifests are fully allocated; budget allocation is order independent', async () => {
  const files = [{path:'data/book.txt',byte_length:2000000},{path:'contributions/x/contribution.json',byte_length:9000},{path:'tool.py',byte_length:15000}];
  const budget = artifactBudgets(files);
  assert.deepEqual([...budget], [...artifactBudgets([...files].reverse())]);
  assert.equal(budget.get('tool.py'),15000); assert.equal(budget.get('contributions/x/contribution.json'),9000);
  assert.ok([...budget.values()].reduce((a,b)=>a+b,0)<=96000);
  await assert.rejects(inspectTextArtifact('tool.py', bytes('x'.repeat(10000)),2000), /requires_full_text/);
  await assert.rejects(inspectTextArtifact('data.txt',new Uint8Array(8000001)),/storage_limit/);
});
test('derived views require profile opt-in and source/representation integrity', async () => {
  const input = await gradingInput(); const file = await inspectTextArtifact('data/corpus.txt', bytes('abc\n'.repeat(30000)), 3000); input.files.push(file);
  assert.ok((await preflight(input)).some(i=>i.code==='inspection_gap'));
  input.profile = {...input.profile,max_file_bytes:4000000,max_total_bytes:24000000,settings:{...input.profile.settings,artifact_handling:'bounded-text-v1'}};
  assert.deepEqual(await preflight(input),[]);
  file.sha256='0'.repeat(64); assert.ok((await preflight(input)).some(i=>i.code==='representation_binding'));
});
test('notebook attachments and embedded visual payloads stay blocked; plain notebooks remain visible', async () => {
  await assert.rejects(inspectTextArtifact('study.ipynb',bytes(JSON.stringify({cells:[{attachments:{a:{'image/png':'AAAA'}}}]}))),/embedded_content/);
  assert.equal((await inspectTextArtifact('study.ipynb', bytes(JSON.stringify({cells:[{source:['print(1)'],outputs:[]}]})))).inspection,'complete');
});


test('XML is fully parsed without DTD/entity expansion and can be represented within a published budget', async () => {
 const xml = bytes('<root>' + '<word>test &amp; evidence</word>'.repeat(50000) + '</root>');
 const view = await inspectTextArtifact('data/control.xml', xml, 3000);assert.equal(JSON.parse(view.content!).structure.elements, 50001);
 await assert.rejects(inspectTextArtifact('data/control.xml',bytes('<!DOCTYPE x [<!ENTITY a SYSTEM "file:///secret">]><x>&a;</x>')), /dtd_prohibited/);
 await assert.rejects(inspectTextArtifact('data/control.xml',bytes('<root><bad></root>')), /invalid_xml/);
 assert.equal(artifactBudgets([{path:'report.md',byte_length:100000}],1000000).get('report.md'),100000);
 assert.throws(()=>artifactBudgets([{path:'report.md',byte_length:100000}]),/model_evidence_limit/);
});
